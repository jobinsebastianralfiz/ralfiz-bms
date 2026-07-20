"""LangGraph supervisor: route a question to exactly one whitelisted tool.

The model's only capability here is choosing a tool name and its arguments.
It never sees a database connection, never composes SQL, and cannot reach any
function outside TOOL_REGISTRY. Each tool is bound to the caller's PulseScope
by closure before the model ever sees it, so there is no argument the model
could supply that would widen its own permissions.

Adaptive thinking is deliberately not enabled: this is a routing decision made
in one hop, and thinking would add latency for no gain. If the supervisor later
grows multi-step planning, that is the point to revisit it.
"""

import json
import logging
from functools import partial
from typing import Optional

from django.conf import settings
from pydantic import BaseModel, Field

from .tools import TOOL_REGISTRY

logger = logging.getLogger(__name__)


class PulseConfigurationError(RuntimeError):
    """Raised when PULSE is called without a usable model configuration."""


# --------------------------------------------------------------------------
# Argument schemas. Tools with no arguments get None.
# --------------------------------------------------------------------------


class ProjectArgs(BaseModel):
    project_id: str = Field(description='UUID of the project.')


class LeadArgs(BaseModel):
    # crm.Lead uses an integer primary key, unlike the UUID keys used
    # throughout core and employees.
    lead_id: int = Field(description='Numeric ID of the lead.')


class FollowupArgs(BaseModel):
    limit: int = Field(default=25, description='Maximum leads to return (1-100).')


class AttendanceArgs(BaseModel):
    date: Optional[str] = Field(
        default=None,
        description='Day to report on, ISO format YYYY-MM-DD. Omit for today.',
    )


#: name -> (description shown to the model, pydantic args schema or None)
#:
#: Descriptions are prescriptive about *when* to call, not just what the tool
#: does -- that measurably improves tool selection.
TOOL_SPECS = {
    'get_projects_needing_attention': (
        'Call when asked which projects are stuck, paused, slipping, late, at '
        'risk, or need attention. Returns projects that are on hold or past '
        'their deadline. Note the system does not record a "blocked" state, so '
        'this is the closest available answer.',
        None,
    ),
    'count_projects_by_status': (
        'Call for counts of projects overall or per status, e.g. "how many '
        'active projects", "how many are in progress", "project breakdown".',
        None,
    ),
    'get_project_summary': (
        'Call for detail on ONE named project: its status, client, team, task '
        'counts and billing. Requires the project UUID.',
        ProjectArgs,
    ),
    'get_team_for_project': (
        'Call when asked who is working on, assigned to, or staffed on a '
        'specific project. Requires the project UUID.',
        ProjectArgs,
    ),
    'get_overdue_invoices': (
        'Call when asked about late payments, overdue invoices, or who owes '
        'money past the due date.',
        None,
    ),
    'get_outstanding_receivables': (
        'Call when asked how much money is owed to the business in total, or '
        'about receivables, unpaid balance, or cash expected.',
        None,
    ),
    'get_leads_needing_followup': (
        'Call when asked which leads need chasing, which follow-ups are due or '
        'overdue, or which leads are hot or a priority today. The system has no '
        'lead score, so priority means a follow-up date that has arrived.',
        FollowupArgs,
    ),
    'get_lead_pipeline_summary': (
        'Call for the shape of the sales pipeline: how many leads exist and '
        'how they are distributed across stages.',
        None,
    ),
    'get_lead_quotes': (
        'Call when asked what has been quoted to a specific lead. Requires the '
        'numeric lead ID. Returns structured quotes only, not uploaded files.',
        LeadArgs,
    ),
    'get_pending_leave_requests': (
        'Call when asked about leave awaiting approval, pending time-off '
        'requests, or who has applied for leave.',
        None,
    ),
    'get_attendance_summary': (
        'Call when asked who is in, present, absent, late or working remotely '
        'on a given day. Defaults to today.',
        AttendanceArgs,
    ),
}

SYSTEM_PROMPT = """You are PULSE, the command centre for Ralfiz Technologies' \
business management system.

You answer questions about the business by calling exactly one of the tools \
provided. You have no other access to data.

Rules:
- Always call a tool before answering a question about the business. Never \
answer from memory or assumption.
- If no tool fits the question, say plainly what you cannot answer and name \
what you can. Do not guess.
- Some concepts the user may ask for are not recorded by this system. There is \
no "blocked" project state and no lead priority score. If asked for those, use \
the closest tool and say explicitly what you actually measured.
- Answer in two or three sentences. Lead with the number or the finding. The \
structured data is returned to the interface separately, so do not reproduce \
long lists in prose -- summarise and give the headline figures.
- Amounts are Indian Rupees.
"""


def build_tools(scope):
    """Bind every whitelisted function to this caller's scope."""
    from langchain_core.tools import StructuredTool

    tools = []
    for name, (description, args_schema) in TOOL_SPECS.items():
        fn = TOOL_REGISTRY[name]
        bound = partial(fn, scope)

        if args_schema is None:
            # StructuredTool needs a callable with no required params here.
            tools.append(StructuredTool.from_function(
                func=lambda _bound=bound: _bound(),
                name=name,
                description=description,
            ))
        else:
            tools.append(StructuredTool.from_function(
                func=bound,
                name=name,
                description=description,
                args_schema=args_schema,
            ))
    return tools


def _build_model():
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
    if not api_key:
        raise PulseConfigurationError(
            'ANTHROPIC_API_KEY is not set. PULSE cannot answer questions '
            'until it is configured in the environment.'
        )

    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(
        model=getattr(settings, 'PULSE_MODEL', 'claude-opus-4-8'),
        api_key=api_key,
        max_tokens=2048,
    )


def ask(query: str, scope) -> dict:
    """Route one question and return {answer, intent, data}.

    intent is the tool actually called (None if the model answered without
    one). data is that tool's structured output, passed through untouched so
    the UI can render cards from it.
    """
    from langgraph.prebuilt import create_react_agent

    model = _build_model()
    agent = create_react_agent(model, build_tools(scope), prompt=SYSTEM_PROMPT)

    result = agent.invoke({'messages': [('user', query)]})
    messages = result.get('messages', [])

    intent = None
    data = None

    # Walk backwards for the last tool actually executed.
    for message in reversed(messages):
        if getattr(message, 'type', None) == 'tool':
            intent = getattr(message, 'name', None)
            raw = message.content
            try:
                data = json.loads(raw) if isinstance(raw, str) else raw
            except (TypeError, ValueError):
                data = {'raw': str(raw)}
            break

    answer = ''
    if messages:
        last = messages[-1]
        content = getattr(last, 'content', '')
        if isinstance(content, list):
            # Content blocks -- keep the text ones.
            answer = ''.join(
                block.get('text', '')
                for block in content
                if isinstance(block, dict)
            ).strip()
        else:
            answer = str(content).strip()

    return {'answer': answer, 'intent': intent, 'data': data}
