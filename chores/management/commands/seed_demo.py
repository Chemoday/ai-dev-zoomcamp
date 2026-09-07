"""Idempotent demo-data seeder for the ephemeral free-tier deployment.

Run on every container boot (after `migrate`, before gunicorn starts).
Wipes and recreates a fixed dataset rather than get_or_create-forever:
since the goal is always a clean baseline on boot, wipe-and-reseed is
more robust against a previous visitor's edits lingering in a
still-warm (not-yet-spun-down) container than any merge/upsert would be.
"""

import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from chores.models import Household, Membership, SubTask, Task, Zone

DEMO_USERNAMES = ["alice", "bob", "carol", "dave", "erin"]


class Command(BaseCommand):
    help = "Wipe and recreate the fixed demo dataset. Safe to run on every boot."

    def handle(self, *args, **options):
        password = os.environ.get("DEMO_PASSWORD", "demo-pass-not-for-prod")

        with transaction.atomic():
            self._wipe()
            users = self._create_users(password)
            self._seed_p2p_household(users)
            self._seed_hierarchical_household(users)

        self.stdout.write(self.style.SUCCESS("Demo data seeded."))

    def _wipe(self):
        Household.objects.all().delete()  # cascades to Membership/Zone/Task/SubTask
        User.objects.filter(username__in=DEMO_USERNAMES).delete()

    def _create_users(self, password):
        return {
            username: User.objects.create_user(
                username=username, password=password, email=f"{username}@example.com"
            )
            for username in DEMO_USERNAMES
        }

    def _seed_p2p_household(self, users):
        household = Household.objects.create(name="Riverside Flatshare", mode=Household.Mode.P2P)
        Membership.objects.create(user=users["alice"], household=household, role=Membership.Role.ADMIN)
        Membership.objects.create(user=users["bob"], household=household, role=Membership.Role.MEMBER)
        Membership.objects.create(
            user=users["carol"], household=household, role=Membership.Role.MEMBER, is_away=True
        )

        kitchen = Zone.objects.create(household=household, name="Kitchen", is_shared=True)
        living = Zone.objects.create(household=household, name="Living room", is_shared=True)

        Task.objects.create(zone=kitchen, title="Wash dishes", status=Task.Status.TODO)
        Task.objects.create(
            zone=kitchen, title="Take out recycling", status=Task.Status.IN_PROGRESS, assignee=users["bob"]
        )
        Task.objects.create(
            zone=living, title="Vacuum carpet", status=Task.Status.BLOCKED,
            blocked_reason="Vacuum cleaner broken", assignee=users["alice"],
        )
        Task.objects.create(zone=kitchen, title="Buy groceries", status=Task.Status.DONE, assignee=users["alice"])
        Task.objects.create(
            zone=kitchen, title="Clean fridge", status=Task.Status.TODO,
            is_recurring=True, interval_days=14,
        )
        subtasked = Task.objects.create(zone=living, title="Deep clean bathroom", status=Task.Status.TODO)
        SubTask.objects.create(task=subtasked, title="Mirror")
        SubTask.objects.create(task=subtasked, title="Toilet")
        SubTask.objects.create(task=subtasked, title="Floor", is_completed=True)

    def _seed_hierarchical_household(self, users):
        household = Household.objects.create(name="Maple Street House", mode=Household.Mode.HIERARCHICAL)
        Membership.objects.create(user=users["dave"], household=household, role=Membership.Role.ADMIN)
        Membership.objects.create(user=users["erin"], household=household, role=Membership.Role.MEMBER)
        # alice is a member here too, admin elsewhere — demonstrates per-household roles.
        Membership.objects.create(user=users["alice"], household=household, role=Membership.Role.MEMBER)

        bathroom = Zone.objects.create(household=household, name="Bathroom", is_shared=True)
        garden = Zone.objects.create(household=household, name="Garden", is_shared=False)
        garden.residents.add(users["dave"])

        Task.objects.create(zone=bathroom, title="Scrub tub", status=Task.Status.TODO, requires_approval=True)
        Task.objects.create(
            zone=garden, title="Mow lawn", status=Task.Status.IN_PROGRESS,
            assignee=users["erin"], requires_approval=True,
        )
        Task.objects.create(
            zone=bathroom, title="Restock towels", status=Task.Status.BLOCKED,
            blocked_reason="Waiting on delivery", assignee=users["dave"],
        )
        Task.objects.create(
            zone=garden, title="Trim hedges", status=Task.Status.IN_PROGRESS,
            assignee=users["erin"], requires_approval=True, awaiting_approval=True,
        )
        Task.objects.create(
            zone=bathroom, title="Replace shower curtain", status=Task.Status.DONE, assignee=users["dave"]
        )
