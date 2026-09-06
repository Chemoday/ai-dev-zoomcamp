from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Household, Membership, Task, Zone


class APITestCaseWithAuth(APITestCase):
    def authenticate(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")


class AuthTests(APITestCaseWithAuth):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pw12345")

    def test_unauthenticated_request_is_rejected(self):
        response = self.client.get("/api/tasks/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_endpoint_returns_token_for_valid_credentials(self):
        response = self.client.post(
            "/api/token/", {"username": "alice", "password": "pw12345"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)

    def test_token_endpoint_rejects_bad_credentials(self):
        response = self.client.post(
            "/api/token/", {"username": "alice", "password": "wrong"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class HouseholdScopingTests(APITestCaseWithAuth):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pw12345")
        self.outsider = User.objects.create_user(username="bob", password="pw12345")

        self.household = Household.objects.create(name="Casa", mode=Household.Mode.P2P)
        Membership.objects.create(
            user=self.user, household=self.household, role=Membership.Role.MEMBER
        )
        self.zone = Zone.objects.create(household=self.household, name="Kitchen")
        self.task = Task.objects.create(zone=self.zone, title="Dishes")

        self.other_household = Household.objects.create(name="Other", mode=Household.Mode.P2P)
        Membership.objects.create(
            user=self.outsider, household=self.other_household, role=Membership.Role.MEMBER
        )

    def test_user_only_sees_own_households(self):
        self.authenticate(self.user)
        response = self.client.get("/api/households/")
        ids = [h["id"] for h in response.data]
        self.assertEqual(ids, [self.household.id])

    def test_user_only_sees_own_tasks_in_list(self):
        self.authenticate(self.outsider)
        response = self.client.get("/api/tasks/")
        self.assertEqual(response.data, [])

    def test_fetching_other_households_task_returns_404(self):
        self.authenticate(self.outsider)
        response = self.client.get(f"/api/tasks/{self.task.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_creating_household_makes_creator_admin_member(self):
        self.authenticate(self.user)
        response = self.client.post("/api/households/", {"name": "New House", "mode": "P2P"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        membership = Membership.objects.get(user=self.user, household_id=response.data["id"])
        self.assertTrue(membership.is_admin)


class MeAndUsersTests(APITestCaseWithAuth):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", password="pw12345", email="alice@example.com"
        )
        self.housemate = User.objects.create_user(username="carol", password="pw12345")
        self.outsider = User.objects.create_user(username="bob", password="pw12345")

        self.household = Household.objects.create(name="Casa", mode=Household.Mode.P2P)
        Membership.objects.create(
            user=self.user, household=self.household, role=Membership.Role.MEMBER
        )
        Membership.objects.create(
            user=self.housemate, household=self.household, role=Membership.Role.MEMBER
        )

        self.other_household = Household.objects.create(name="Other", mode=Household.Mode.P2P)
        Membership.objects.create(
            user=self.outsider, household=self.other_household, role=Membership.Role.MEMBER
        )

    def test_me_returns_own_identity(self):
        self.authenticate(self.user)
        response = self.client.get("/api/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.user.id)
        self.assertEqual(response.data["username"], "alice")
        self.assertEqual(response.data["email"], "alice@example.com")

    def test_users_list_includes_housemate_but_not_outsider(self):
        self.authenticate(self.user)
        response = self.client.get("/api/users/")
        usernames = {row["username"] for row in response.data}
        self.assertIn("alice", usernames)
        self.assertIn("carol", usernames)
        self.assertNotIn("bob", usernames)


class TaskLifecycleAPITests(APITestCaseWithAuth):
    def setUp(self):
        self.admin_user = User.objects.create_user(username="admin", password="pw12345")
        self.member_user = User.objects.create_user(username="member", password="pw12345")
        self.other_member = User.objects.create_user(username="other", password="pw12345")

        self.household = Household.objects.create(
            name="Family House", mode=Household.Mode.HIERARCHICAL
        )
        Membership.objects.create(
            user=self.admin_user, household=self.household, role=Membership.Role.ADMIN
        )
        Membership.objects.create(
            user=self.member_user, household=self.household, role=Membership.Role.MEMBER
        )
        Membership.objects.create(
            user=self.other_member, household=self.household, role=Membership.Role.MEMBER
        )
        self.zone = Zone.objects.create(household=self.household, name="Kitchen")

    def make_task(self, **kwargs):
        return Task.objects.create(zone=self.zone, title="Dishes", **kwargs)

    def test_start_assigns_caller_and_moves_in_progress(self):
        task = self.make_task()
        self.authenticate(self.member_user)
        response = self.client.post(f"/api/tasks/{task.id}/start/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.IN_PROGRESS)
        self.assertEqual(task.assignee_id, self.member_user.id)

    def test_start_twice_returns_400_invalid_transition(self):
        task = self.make_task(status=Task.Status.DONE)
        self.authenticate(self.member_user)
        response = self.client.post(f"/api/tasks/{task.id}/start/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_drop_by_assignee_succeeds(self):
        task = self.make_task()
        self.authenticate(self.member_user)
        self.client.post(f"/api/tasks/{task.id}/start/")
        response = self.client.post(f"/api/tasks/{task.id}/drop/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_drop_by_non_assignee_returns_403(self):
        task = self.make_task()
        self.authenticate(self.member_user)
        self.client.post(f"/api/tasks/{task.id}/start/")
        self.authenticate(self.other_member)
        response = self.client.post(f"/api/tasks/{task.id}/drop/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_drop_by_admin_override_succeeds(self):
        task = self.make_task()
        self.authenticate(self.member_user)
        self.client.post(f"/api/tasks/{task.id}/start/")
        self.authenticate(self.admin_user)
        response = self.client.post(f"/api/tasks/{task.id}/drop/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_block_without_reason_returns_400(self):
        task = self.make_task()
        self.authenticate(self.member_user)
        response = self.client.post(f"/api/tasks/{task.id}/block/", {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_block_by_non_assignee_when_assigned_returns_403(self):
        task = self.make_task()
        self.authenticate(self.member_user)
        self.client.post(f"/api/tasks/{task.id}/start/")
        self.authenticate(self.other_member)
        response = self.client.post(f"/api/tasks/{task.id}/block/", {"reason": "No supplies"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unblock_returns_to_in_progress(self):
        task = self.make_task()
        self.authenticate(self.member_user)
        self.client.post(f"/api/tasks/{task.id}/start/")
        self.client.post(f"/api/tasks/{task.id}/block/", {"reason": "No hot water"})
        response = self.client.post(f"/api/tasks/{task.id}/unblock/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.IN_PROGRESS)

    def test_complete_by_non_assignee_returns_403(self):
        task = self.make_task()
        self.authenticate(self.member_user)
        self.client.post(f"/api/tasks/{task.id}/start/")
        self.authenticate(self.other_member)
        response = self.client.post(f"/api/tasks/{task.id}/complete/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_complete_requiring_approval_leaves_awaiting_then_admin_approves(self):
        task = self.make_task(requires_approval=True)
        self.authenticate(self.member_user)
        self.client.post(f"/api/tasks/{task.id}/start/")
        response = self.client.post(f"/api/tasks/{task.id}/complete/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertTrue(task.awaiting_approval)
        self.assertEqual(task.status, Task.Status.IN_PROGRESS)

        self.authenticate(self.admin_user)
        response = self.client.post(f"/api/tasks/{task.id}/approve/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.DONE)

    def test_non_admin_approve_returns_403(self):
        task = self.make_task(requires_approval=True)
        self.authenticate(self.member_user)
        self.client.post(f"/api/tasks/{task.id}/start/")
        self.client.post(f"/api/tasks/{task.id}/complete/")
        response = self.client.post(f"/api/tasks/{task.id}/approve/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_approve_when_not_awaiting_returns_400(self):
        task = self.make_task()
        self.authenticate(self.admin_user)
        response = self.client.post(f"/api/tasks/{task.id}/approve/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_p2p_household_ignores_requires_approval_end_to_end(self):
        p2p_household = Household.objects.create(name="Flatshare", mode=Household.Mode.P2P)
        Membership.objects.create(
            user=self.member_user, household=p2p_household, role=Membership.Role.MEMBER
        )
        p2p_zone = Zone.objects.create(household=p2p_household, name="Bathroom")
        task = Task.objects.create(zone=p2p_zone, title="Clean sink", requires_approval=True)

        self.authenticate(self.member_user)
        self.client.post(f"/api/tasks/{task.id}/start/")
        response = self.client.post(f"/api/tasks/{task.id}/complete/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.DONE)
        self.assertFalse(task.awaiting_approval)
