"""Governance rules shared by any interface layer (admin, views, or API).

Kept independent of Task's lifecycle methods (Phase 4) and of whatever
interface layer Phase 5 ends up using, so both can call into the same
rules without duplicating them.
"""

from .models import Household, Membership


class PermissionDenied(Exception):
    pass


def get_membership(user, household):
    return Membership.objects.filter(user=user, household=household).first()


def is_admin(user, household) -> bool:
    membership = get_membership(user, household)
    return bool(membership and membership.is_admin)


def task_requires_admin_approval(task) -> bool:
    """P2P households have equal permissions, so a task's own
    ``requires_approval`` flag is only honored in Hierarchical households.
    """
    household = task.zone.household
    return task.requires_approval and household.mode == Household.Mode.HIERARCHICAL


def is_available_for_assignment(user, household) -> bool:
    membership = get_membership(user, household)
    return bool(membership and not membership.is_away)


def assign_task(task, user):
    from .errors import Errors  # deferred: errors.py imports this module at load time

    household = task.zone.household
    Errors.Permission.require_available(user, household)
    task.assignee = user
    task.save(update_fields=["assignee"])
    return task


def can_manage_task(user, task) -> bool:
    """Whether `user` may drop/block/unblock/complete this task.

    The assignee owns a claimed task's lifecycle; an admin can always
    override. An unclaimed task (no assignee) is fair game for any
    household member. Relies on the invariant that a task only ever
    gets an assignee via `assign_task`, so "assignee or admin" is
    always the right gate once one is set.
    """
    household = task.zone.household
    if task.assignee_id and task.assignee_id != user.id:
        return is_admin(user, household)
    return bool(get_membership(user, household))
