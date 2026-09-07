from datetime import timedelta

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from . import lifecycle, permissions
from .errors import Errors
from .models import Household, Membership, Task, Zone


class MembershipModelTests(TestCase):
    def test_is_admin_property(self):
        user = User.objects.create(username="alice")
        household = Household.objects.create(name="Casa", mode=Household.Mode.P2P)
        admin_membership = Membership.objects.create(
            user=user, household=household, role=Membership.Role.ADMIN
        )
        self.assertTrue(admin_membership.is_admin)

        member = User.objects.create(username="bob")
        member_membership = Membership.objects.create(
            user=member, household=household, role=Membership.Role.MEMBER
        )
        self.assertFalse(member_membership.is_admin)

    def test_unique_together_prevents_duplicate_membership(self):
        user = User.objects.create(username="carol")
        household = Household.objects.create(name="Casa", mode=Household.Mode.P2P)
        Membership.objects.create(user=user, household=household, role=Membership.Role.MEMBER)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Membership.objects.create(user=user, household=household, role=Membership.Role.ADMIN)


class TaskOverdueTests(TestCase):
    def setUp(self):
        household = Household.objects.create(name="Casa", mode=Household.Mode.P2P)
        self.zone = Zone.objects.create(household=household, name="Kitchen")

    def test_overdue_when_deadline_passed_and_not_done(self):
        task = Task.objects.create(
            zone=self.zone, title="Dishes", deadline=timezone.now() - timedelta(days=1)
        )
        self.assertTrue(task.is_overdue)

    def test_not_overdue_when_done(self):
        task = Task.objects.create(
            zone=self.zone,
            title="Dishes",
            deadline=timezone.now() - timedelta(days=1),
            status=Task.Status.DONE,
        )
        self.assertFalse(task.is_overdue)

    def test_not_overdue_without_deadline(self):
        task = Task.objects.create(zone=self.zone, title="Dishes")
        self.assertFalse(task.is_overdue)

    def test_not_overdue_before_deadline(self):
        task = Task.objects.create(
            zone=self.zone, title="Dishes", deadline=timezone.now() + timedelta(days=1)
        )
        self.assertFalse(task.is_overdue)


class PermissionsTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create(username="admin")
        self.member_user = User.objects.create(username="member")
        self.away_user = User.objects.create(username="away")

        self.hierarchical = Household.objects.create(
            name="Family House", mode=Household.Mode.HIERARCHICAL
        )
        Membership.objects.create(
            user=self.admin_user, household=self.hierarchical, role=Membership.Role.ADMIN
        )
        Membership.objects.create(
            user=self.member_user, household=self.hierarchical, role=Membership.Role.MEMBER
        )
        Membership.objects.create(
            user=self.away_user,
            household=self.hierarchical,
            role=Membership.Role.MEMBER,
            is_away=True,
        )
        self.zone = Zone.objects.create(household=self.hierarchical, name="Kitchen")

        self.p2p = Household.objects.create(name="Flatshare", mode=Household.Mode.P2P)
        Membership.objects.create(
            user=self.member_user, household=self.p2p, role=Membership.Role.MEMBER
        )
        self.p2p_zone = Zone.objects.create(household=self.p2p, name="Bathroom")

    def test_is_admin(self):
        self.assertTrue(permissions.is_admin(self.admin_user, self.hierarchical))
        self.assertFalse(permissions.is_admin(self.member_user, self.hierarchical))

    def test_require_admin_raises_for_non_admin(self):
        with self.assertRaises(permissions.PermissionDenied):
            Errors.Permission.require_admin(self.member_user, self.hierarchical)
        Errors.Permission.require_admin(self.admin_user, self.hierarchical)  # no raise

    def test_hierarchical_household_honors_requires_approval(self):
        task = Task.objects.create(zone=self.zone, title="Chore", requires_approval=True)
        self.assertTrue(permissions.task_requires_admin_approval(task))

    def test_p2p_household_ignores_requires_approval(self):
        task = Task.objects.create(zone=self.p2p_zone, title="Chore", requires_approval=True)
        self.assertFalse(permissions.task_requires_admin_approval(task))

    def test_is_available_for_assignment_excludes_away_members(self):
        self.assertTrue(permissions.is_available_for_assignment(self.member_user, self.hierarchical))
        self.assertFalse(permissions.is_available_for_assignment(self.away_user, self.hierarchical))

    def test_assign_task_rejects_away_member(self):
        task = Task.objects.create(zone=self.zone, title="Chore")
        with self.assertRaises(permissions.PermissionDenied):
            permissions.assign_task(task, self.away_user)

    def test_assign_task_succeeds_for_available_member(self):
        task = Task.objects.create(zone=self.zone, title="Chore")
        permissions.assign_task(task, self.member_user)
        self.assertEqual(task.assignee_id, self.member_user.id)

    def test_is_admin_is_scoped_per_household(self):
        # member_user is MEMBER in self.hierarchical but ADMIN elsewhere —
        # proves role lookups don't leak across households.
        other_household = Household.objects.create(name="Other House", mode=Household.Mode.HIERARCHICAL)
        Membership.objects.create(
            user=self.member_user, household=other_household, role=Membership.Role.ADMIN
        )
        self.assertFalse(permissions.is_admin(self.member_user, self.hierarchical))
        self.assertTrue(permissions.is_admin(self.member_user, other_household))

    def test_is_available_for_assignment_is_scoped_per_household(self):
        # away_user is away in self.hierarchical but not away elsewhere —
        # proves availability lookups don't leak across households.
        other_household = Household.objects.create(name="Other House", mode=Household.Mode.P2P)
        Membership.objects.create(
            user=self.away_user, household=other_household, role=Membership.Role.MEMBER, is_away=False
        )
        self.assertFalse(permissions.is_available_for_assignment(self.away_user, self.hierarchical))
        self.assertTrue(permissions.is_available_for_assignment(self.away_user, other_household))


class LifecycleTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create(username="admin")
        self.member_user = User.objects.create(username="member")

        self.household = Household.objects.create(
            name="Family House", mode=Household.Mode.HIERARCHICAL
        )
        Membership.objects.create(
            user=self.admin_user, household=self.household, role=Membership.Role.ADMIN
        )
        Membership.objects.create(
            user=self.member_user, household=self.household, role=Membership.Role.MEMBER
        )
        self.zone = Zone.objects.create(household=self.household, name="Kitchen")

    def test_start_task_assigns_and_moves_in_progress(self):
        task = Task.objects.create(zone=self.zone, title="Dishes")
        lifecycle.start_task(task, self.member_user)
        self.assertEqual(task.status, Task.Status.IN_PROGRESS)
        self.assertEqual(task.assignee_id, self.member_user.id)

    def test_start_task_invalid_from_non_todo(self):
        task = Task.objects.create(zone=self.zone, title="Dishes", status=Task.Status.DONE)
        with self.assertRaises(lifecycle.InvalidTransition):
            lifecycle.start_task(task, self.member_user)

    def test_drop_task_returns_to_pool(self):
        task = Task.objects.create(zone=self.zone, title="Dishes")
        lifecycle.start_task(task, self.member_user)
        lifecycle.drop_task(task, self.member_user)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.TODO)
        self.assertIsNone(task.assignee)

    def test_block_requires_reason(self):
        task = Task.objects.create(zone=self.zone, title="Dishes")
        with self.assertRaises(ValueError):
            lifecycle.block_task(task, self.member_user, "")

    def test_unblock_task_without_assignee_returns_to_todo(self):
        task = Task.objects.create(zone=self.zone, title="Dishes")
        lifecycle.block_task(task, self.member_user, "No supplies")
        lifecycle.unblock_task(task, self.member_user)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.TODO)
        self.assertEqual(task.blocked_reason, "")

    def test_start_task_rejects_away_user(self):
        away_user = User.objects.create(username="away")
        Membership.objects.create(
            user=away_user, household=self.household, role=Membership.Role.MEMBER, is_away=True
        )
        task = Task.objects.create(zone=self.zone, title="Dishes")
        with self.assertRaises(permissions.PermissionDenied):
            lifecycle.start_task(task, away_user)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.TODO)
        self.assertIsNone(task.assignee)

    def test_block_and_unblock_cycle(self):
        task = Task.objects.create(zone=self.zone, title="Dishes")
        lifecycle.start_task(task, self.member_user)
        lifecycle.block_task(task, self.member_user, "No hot water")
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.BLOCKED)
        self.assertEqual(task.blocked_reason, "No hot water")

        lifecycle.unblock_task(task, self.member_user)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.IN_PROGRESS)
        self.assertEqual(task.blocked_reason, "")

    def test_drop_task_rejects_non_assignee(self):
        other_member = User.objects.create(username="other")
        Membership.objects.create(
            user=other_member, household=self.household, role=Membership.Role.MEMBER
        )
        task = Task.objects.create(zone=self.zone, title="Dishes")
        lifecycle.start_task(task, self.member_user)
        with self.assertRaises(permissions.PermissionDenied):
            lifecycle.drop_task(task, other_member)

    def test_drop_task_allows_admin_override(self):
        task = Task.objects.create(zone=self.zone, title="Dishes")
        lifecycle.start_task(task, self.member_user)
        lifecycle.drop_task(task, self.admin_user)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.TODO)
        self.assertIsNone(task.assignee)

    def test_block_task_rejects_non_assignee_when_assigned(self):
        other_member = User.objects.create(username="other")
        Membership.objects.create(
            user=other_member, household=self.household, role=Membership.Role.MEMBER
        )
        task = Task.objects.create(zone=self.zone, title="Dishes")
        lifecycle.start_task(task, self.member_user)
        with self.assertRaises(permissions.PermissionDenied):
            lifecycle.block_task(task, other_member, "No supplies")

    def test_block_task_allows_any_member_when_unassigned(self):
        other_member = User.objects.create(username="other")
        Membership.objects.create(
            user=other_member, household=self.household, role=Membership.Role.MEMBER
        )
        task = Task.objects.create(zone=self.zone, title="Dishes")
        lifecycle.block_task(task, other_member, "No supplies")
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.BLOCKED)

    def test_unblock_task_rejects_non_assignee_when_assigned(self):
        other_member = User.objects.create(username="other")
        Membership.objects.create(
            user=other_member, household=self.household, role=Membership.Role.MEMBER
        )
        task = Task.objects.create(zone=self.zone, title="Dishes")
        lifecycle.start_task(task, self.member_user)
        lifecycle.block_task(task, self.member_user, "No hot water")
        with self.assertRaises(permissions.PermissionDenied):
            lifecycle.unblock_task(task, other_member)

    def test_complete_task_rejects_non_assignee(self):
        other_member = User.objects.create(username="other")
        Membership.objects.create(
            user=other_member, household=self.household, role=Membership.Role.MEMBER
        )
        task = Task.objects.create(zone=self.zone, title="Dishes")
        lifecycle.start_task(task, self.member_user)
        with self.assertRaises(permissions.PermissionDenied):
            lifecycle.complete_task(task, other_member)

    def test_complete_task_allows_admin_override(self):
        task = Task.objects.create(zone=self.zone, title="Dishes")
        lifecycle.start_task(task, self.member_user)
        lifecycle.complete_task(task, self.admin_user)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.DONE)

    def test_complete_without_approval_marks_done(self):
        task = Task.objects.create(zone=self.zone, title="Dishes")
        lifecycle.start_task(task, self.member_user)
        lifecycle.complete_task(task, self.member_user)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.DONE)
        self.assertFalse(task.awaiting_approval)

    def test_complete_with_approval_awaits_admin(self):
        task = Task.objects.create(zone=self.zone, title="Dishes", requires_approval=True)
        lifecycle.start_task(task, self.member_user)
        lifecycle.complete_task(task, self.member_user)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.IN_PROGRESS)
        self.assertTrue(task.awaiting_approval)

    def test_approve_task_requires_admin(self):
        task = Task.objects.create(zone=self.zone, title="Dishes", requires_approval=True)
        lifecycle.start_task(task, self.member_user)
        lifecycle.complete_task(task, self.member_user)
        with self.assertRaises(permissions.PermissionDenied):
            lifecycle.approve_task(task, self.member_user)

    def test_approve_task_marks_done(self):
        task = Task.objects.create(zone=self.zone, title="Dishes", requires_approval=True)
        lifecycle.start_task(task, self.member_user)
        lifecycle.complete_task(task, self.member_user)
        lifecycle.approve_task(task, self.admin_user)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.DONE)
        self.assertFalse(task.awaiting_approval)

    def test_approve_task_rejects_when_not_awaiting(self):
        task = Task.objects.create(zone=self.zone, title="Dishes")
        with self.assertRaises(lifecycle.InvalidTransition):
            lifecycle.approve_task(task, self.admin_user)

    def test_complete_in_p2p_household_ignores_requires_approval(self):
        p2p_household = Household.objects.create(name="Flatshare", mode=Household.Mode.P2P)
        Membership.objects.create(
            user=self.member_user, household=p2p_household, role=Membership.Role.MEMBER
        )
        p2p_zone = Zone.objects.create(household=p2p_household, name="Bathroom")
        task = Task.objects.create(zone=p2p_zone, title="Clean sink", requires_approval=True)

        lifecycle.start_task(task, self.member_user)
        lifecycle.complete_task(task, self.member_user)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.DONE)
        self.assertFalse(task.awaiting_approval)

    def test_approving_recurring_task_spawns_next_occurrence(self):
        deadline = timezone.now()
        task = Task.objects.create(
            zone=self.zone,
            title="Water the plants",
            requires_approval=True,
            is_recurring=True,
            interval_days=7,
            deadline=deadline,
        )
        lifecycle.start_task(task, self.member_user)
        lifecycle.complete_task(task, self.member_user)
        lifecycle.approve_task(task, self.admin_user)

        next_task = Task.objects.exclude(pk=task.pk).get(title="Water the plants")
        self.assertEqual(next_task.status, Task.Status.TODO)
        self.assertEqual(next_task.deadline, deadline + timedelta(days=7))

    def test_completing_recurring_task_spawns_next_occurrence(self):
        deadline = timezone.now()
        task = Task.objects.create(
            zone=self.zone,
            title="Take out trash",
            is_recurring=True,
            interval_days=3,
            deadline=deadline,
        )
        lifecycle.start_task(task, self.member_user)
        lifecycle.complete_task(task, self.member_user)

        next_task = Task.objects.exclude(pk=task.pk).get(title="Take out trash")
        self.assertEqual(next_task.status, Task.Status.TODO)
        self.assertIsNone(next_task.assignee)
        self.assertEqual(next_task.deadline, deadline + timedelta(days=3))

    def test_completing_non_recurring_task_does_not_spawn(self):
        task = Task.objects.create(zone=self.zone, title="One-off cleanup")
        lifecycle.start_task(task, self.member_user)
        lifecycle.complete_task(task, self.member_user)
        self.assertEqual(Task.objects.filter(title="One-off cleanup").count(), 1)
