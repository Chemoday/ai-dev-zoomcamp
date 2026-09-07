"""Centralized error text and check-and-raise helpers for the chores
app, so wording lives in one place and a repeated raise (e.g. the
"cannot manage this task" check shared by four lifecycle actions)
collapses to a single call instead of being copy-pasted at each site.
"""

from rest_framework import serializers

from . import permissions


class InvalidTransition(Exception):
    pass


class Errors:
    class Permission:
        @staticmethod
        def require_admin(user, household):
            if not permissions.is_admin(user, household):
                raise permissions.PermissionDenied(f"{user} is not an admin of {household}")

        @staticmethod
        def require_available(user, household):
            if not permissions.is_available_for_assignment(user, household):
                raise permissions.PermissionDenied(f"{user} is away or not a member of {household}")

    class Task:
        @staticmethod
        def require_can_manage(actor, task):
            if not permissions.can_manage_task(actor, task):
                raise permissions.PermissionDenied(f"{actor} cannot manage this task")

        @staticmethod
        def require_status(task, *valid_statuses, verb):
            if task.status not in valid_statuses:
                raise InvalidTransition(f"Cannot {verb} a task in status {task.status}")

        @staticmethod
        def require_reason(reason):
            if not reason:
                raise ValueError("A reason is required to block a task")

        @staticmethod
        def require_awaiting_approval(task):
            if not task.awaiting_approval:
                raise InvalidTransition("Task is not awaiting approval")

    class Membership:
        @staticmethod
        def require_membership(user, household):
            if not permissions.get_membership(user, household):
                raise serializers.ValidationError("You are not a member of this household.")

        @staticmethod
        def require_admin_for_role_change(user, household):
            if not permissions.is_admin(user, household):
                raise serializers.ValidationError("Only an admin can change a member's role.")

        @staticmethod
        def require_admin_for_away_change(user, household):
            if not permissions.is_admin(user, household):
                raise serializers.ValidationError("You can only change your own away status.")
