"""Task lifecycle mechanics: status transitions, drop/block, completion
and admin-approval, and recurring-task regeneration.

Builds on chores.permissions for anything governance-related (approval
gating, assignment eligibility) so those rules stay defined in one place.
"""

from datetime import timedelta

from django.utils import timezone

from . import permissions
from .errors import Errors, InvalidTransition
from .models import Task


def start_task(task, user):
    """Assign the task to `user` and move it to IN_PROGRESS.

    Only valid from TODO. Raises permissions.PermissionDenied if `user`
    is away or not a member of the task's household.
    """
    Errors.Task.require_status(task, Task.Status.TODO, verb="start")
    permissions.assign_task(task, user)
    task.status = Task.Status.IN_PROGRESS
    task.save(update_fields=["status"])
    return task


def drop_task(task, actor):
    """Release an accepted task back to the unassigned pool."""
    Errors.Task.require_can_manage(actor, task)
    Errors.Task.require_status(task, Task.Status.IN_PROGRESS, verb="drop")
    task.assignee = None
    task.status = Task.Status.TODO
    task.save(update_fields=["assignee", "status"])
    return task


def block_task(task, actor, reason: str):
    Errors.Task.require_can_manage(actor, task)
    Errors.Task.require_reason(reason)
    Errors.Task.require_status(task, Task.Status.TODO, Task.Status.IN_PROGRESS, verb="block")
    task.status = Task.Status.BLOCKED
    task.blocked_reason = reason
    task.save(update_fields=["status", "blocked_reason"])
    return task


def unblock_task(task, actor):
    Errors.Task.require_can_manage(actor, task)
    Errors.Task.require_status(task, Task.Status.BLOCKED, verb="unblock")
    task.status = Task.Status.IN_PROGRESS if task.assignee_id else Task.Status.TODO
    task.blocked_reason = ""
    task.save(update_fields=["status", "blocked_reason"])
    return task


def complete_task(task, actor):
    """Mark a task as completed by `actor`.

    If the task's household requires admin approval for this task, it
    is left in IN_PROGRESS with `awaiting_approval=True` instead of
    being marked DONE outright — see `approve_task`.
    """
    Errors.Task.require_can_manage(actor, task)
    Errors.Task.require_status(task, Task.Status.IN_PROGRESS, verb="complete")

    if permissions.task_requires_admin_approval(task):
        task.awaiting_approval = True
        task.save(update_fields=["awaiting_approval"])
        return task

    return _mark_done(task)


def approve_task(task, admin_user):
    household = task.zone.household
    Errors.Permission.require_admin(admin_user, household)
    Errors.Task.require_awaiting_approval(task)
    return _mark_done(task)


def _mark_done(task):
    task.status = Task.Status.DONE
    task.awaiting_approval = False
    task.save(update_fields=["status", "awaiting_approval"])
    if task.is_recurring and task.interval_days:
        _spawn_next_occurrence(task)
    return task


def _spawn_next_occurrence(task):
    base = task.deadline or timezone.now()
    return Task.objects.create(
        zone=task.zone,
        title=task.title,
        description=task.description,
        requires_approval=task.requires_approval,
        is_recurring=task.is_recurring,
        interval_days=task.interval_days,
        weight=task.weight,
        deadline=base + timedelta(days=task.interval_days),
    )
