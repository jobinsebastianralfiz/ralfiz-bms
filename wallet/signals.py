"""Hooks that turn finished work into pending XP.

They run on every save, whichever screen, API or command did the save. Each is
idempotent (see services.sync_source) and never lets a wallet problem break the
save that triggered it.
"""
import logging
from functools import wraps

from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.dispatch import receiver

from crm.models import Lead
from employees.models import InternAssessment, Payroll, WorkAssignment
from uat.models import UATPlan, UATResult

from . import services

log = logging.getLogger(__name__)


def _safe(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if kwargs.get('raw'):  # loaddata
            return
        try:
            fn(*args, **kwargs)
        except Exception:  # noqa: BLE001
            log.exception('XP wallet hook %s failed', fn.__name__)
    return wrapper


@receiver(post_save, sender=WorkAssignment)
@_safe
def work_saved(sender, instance, **kwargs):
    services.sync_work_assignment(instance)


@receiver(m2m_changed, sender=WorkAssignment.assigned_to.through)
@_safe
def work_people_changed(sender, instance, action, **kwargs):
    if action == 'post_add' and isinstance(instance, WorkAssignment) and instance.status == 'completed':
        services.sync_work_assignment(instance)


@receiver(post_save, sender=UATResult)
@_safe
def uat_result_saved(sender, instance, **kwargs):
    services.sync_uat_tester(instance.case.section.plan, instance.tester)


@receiver(post_save, sender=UATPlan)
@_safe
def uat_plan_saved(sender, instance, created, **kwargs):
    # A reward set (or raised) after someone already finished still reaches them, and marking the
    # plan completed sends every tester's reward for approval.
    if not created and instance.xp_reward:
        for emp in instance.testers.all():
            services.sync_uat_tester(instance, emp)


@receiver(post_save, sender=InternAssessment)
@_safe
def assessment_saved(sender, instance, **kwargs):
    services.sync_assessment(instance)


@receiver(post_save, sender=Lead)
@_safe
def lead_saved(sender, instance, **kwargs):
    services.sync_lead(instance)


@receiver(pre_delete, sender=Payroll)
def payroll_deleted(sender, instance, **kwargs):
    # Not wrapped: if the XP can't be put back, the payslip must not disappear.
    for payout in instance.xp_payouts.filter(status='paid'):
        services.undo_payout(payout, None, 'The payslip it was on was deleted.', payroll_gone=True)
