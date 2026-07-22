"""PULSE ask endpoint.

permission_classes is declared explicitly and must stay that way. This project
sets no DEFAULT_PERMISSION_CLASSES in REST_FRAMEWORK, so a DRF view that omits
it is AllowAny -- which on this endpoint would mean anonymous access to
business-wide revenue data.
"""

import json
import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Project

from .scoping import resolve_scope
from .serializers import (
    AskRequestSerializer,
    AskResponseSerializer,
    DocumentIngestSerializer,
    DocumentSerializer,
)
from .supervisor import PulseConfigurationError, ask
from .tools import (
    ACTIVE_PROJECT_STATUSES,
    get_dashboard_metrics,
    get_dues_and_renewals,
    get_portfolio_graph,
    get_project_summary,
)

logger = logging.getLogger(__name__)


class AskView(APIView):
    """POST a question, get an answer plus the structured data behind it."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=AskRequestSerializer,
        responses={200: AskResponseSerializer},
        tags=['PULSE'],
        summary='Ask PULSE a question about the business',
    )
    def post(self, request):
        serializer = AskRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        query = serializer.validated_data['query']

        scope = resolve_scope(request.user)

        # Authorise BEFORE invoking the model. The tools also call
        # require_business(), but relying on that alone would make
        # authorisation depend on the model deciding to call a tool -- a
        # request that answers from prose, or fails on configuration first,
        # would never reach the gate. Deny early; keep the tool-level check as
        # defence in depth.
        scope.require_business()

        try:
            result = ask(query, scope)
        except PulseConfigurationError as exc:
            logger.error('PULSE not configured: %s', exc)
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except ValueError as exc:
            # Bad tool arguments, e.g. a malformed UUID or date.
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)


def _document_payload(document, chunk_count=None):
    return {
        'id': str(document.id),
        'project': document.project.name,
        'title': document.title,
        'source': document.source,
        'chunks': (
            chunk_count if chunk_count is not None else document.chunks.count()
        ),
        'created_at': document.created_at.isoformat(),
    }


class DocumentsView(APIView):
    """Ingest into and list the PULSE document store.

    POST chunks + embeds text (or an uploaded plain-text file) against a
    project; GET lists what has been ingested. Owner/partner only, same gate
    as every other PULSE surface.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: DocumentSerializer(many=True)},
        tags=['PULSE'],
        summary='List ingested documents',
    )
    def get(self, request):
        scope = resolve_scope(request.user)
        scope.require_business()

        from .models import Document

        documents = Document.objects.select_related('project')
        project_id = request.GET.get('project')
        if project_id:
            documents = documents.filter(project_id=project_id)
        return Response([_document_payload(d) for d in documents])

    @extend_schema(
        request=DocumentIngestSerializer,
        responses={201: DocumentSerializer},
        tags=['PULSE'],
        summary='Ingest a document for semantic search',
    )
    def post(self, request):
        serializer = DocumentIngestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        scope = resolve_scope(request.user)
        scope.require_business()

        project = Project.objects.filter(id=data['project_id']).first()
        if project is None:
            return Response(
                {'detail': 'No project with that ID.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        text = data.get('text', '')
        source = data.get('source', '')
        upload = data.get('file')
        if upload is not None:
            from .ingestion import TEXT_EXTENSIONS

            name = upload.name or ''
            if not name.lower().endswith(TEXT_EXTENSIONS):
                return Response(
                    {'detail': 'Only plain-text files are supported: %s'
                               % ', '.join(TEXT_EXTENSIONS)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                text = upload.read().decode('utf-8', errors='replace')
            except Exception:
                return Response(
                    {'detail': 'Could not read the uploaded file as text.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            source = source or name
        source = source or 'pasted text'

        from .embeddings import EmbeddingConfigurationError
        from .ingestion import ingest_document

        try:
            document = ingest_document(
                scope, project, data['title'], text, source=source
            )
        except EmbeddingConfigurationError as exc:
            logger.error('PULSE embeddings not configured: %s', exc)
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            _document_payload(document),
            status=status.HTTP_201_CREATED,
        )


@method_decorator(login_required, name='dispatch')
class CommandCenterView(View):
    """The PULSE screen itself.

    Server-renders the initial project so the canvas has something real to draw
    on first paint rather than flashing an empty state while JS fetches.
    """

    template_name = 'pulse/command_center.html'

    def get(self, request):
        scope = resolve_scope(request.user)
        if not scope.can_query_business:
            # Send non-owners to the legacy dashboard, NOT to '/'. The
            # constellation is now mounted at '/', so redirecting there would
            # loop forever.
            return redirect('dashboard-legacy')

        projects = list(
            Project.objects
            .filter(status__in=ACTIVE_PROJECT_STATUSES)
            .select_related('client')
            .order_by('deadline', 'name')
        )
        if not projects:
            projects = list(
                Project.objects.exclude(status__in=('completed', 'cancelled'))
                .select_related('client')
                .order_by('name')[:20]
            )

        requested = request.GET.get('project')
        current = None
        if requested:
            current = next((p for p in projects if str(p.id) == requested), None)
        if current is None and projects:
            current = projects[0]

        summary = get_project_summary(scope, str(current.id)) if current else None

        return render(request, self.template_name, {
            'projects': [
                {'id': str(p.id), 'name': p.name,
                 'client': p.client.name if p.client else ''}
                for p in projects
            ],
            'summary_json': json.dumps(summary),
            'operator': scope.display_name,
        })


@method_decorator(login_required, name='dispatch')
class GraphDashboardView(View):
    """The portfolio constellation: the whole business as one graph."""

    template_name = 'pulse/graph_dashboard.html'

    def get(self, request):
        scope = resolve_scope(request.user)
        if not scope.can_query_business:
            # Must NOT be '/': this view is mounted there, so redirecting to
            # '/' sends a non-owner straight back into this branch forever.
            return redirect('dashboard-legacy')

        graph = get_portfolio_graph(scope)

        return render(request, self.template_name, {
            'graph_json': json.dumps(graph),
            'nodes': graph['nodes'],
            'legend': graph['legend'],
            'core': graph['core'],
            'metrics': get_dashboard_metrics(scope),
            'dues': get_dues_and_renewals(scope),
            'operator': scope.display_name,
        })
