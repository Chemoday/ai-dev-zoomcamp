from django.conf import settings
from django.db import models
from django.utils import timezone


class Household(models.Model):
    class Mode(models.TextChoices):
        P2P = "P2P", "Peer-to-peer"
        HIERARCHICAL = "HIERARCHICAL", "Hierarchical"

    name = models.CharField(max_length=255)
    mode = models.CharField(max_length=20, choices=Mode.choices, default=Mode.P2P)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Membership(models.Model):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        MEMBER = "MEMBER", "Member"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    is_away = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "household")

    def __str__(self):
        return f"{self.user} @ {self.household} ({self.role})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN


class Zone(models.Model):
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="zones")
    name = models.CharField(max_length=255)
    is_shared = models.BooleanField(default=True)
    residents = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="zones", blank=True)

    def __str__(self):
        return f"{self.name} ({self.household})"


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = "TODO", "To do"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        BLOCKED = "BLOCKED", "Blocked"
        DONE = "DONE", "Done"

    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="tasks",
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO)
    blocked_reason = models.CharField(max_length=255, blank=True)
    requires_approval = models.BooleanField(default=False)
    awaiting_approval = models.BooleanField(default=False)
    is_recurring = models.BooleanField(default=False)
    interval_days = models.PositiveIntegerField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    weight = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        if self.deadline is None or self.status == self.Status.DONE:
            return False
        return self.deadline < timezone.now()


class SubTask(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="subtasks")
    title = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title
