from django.contrib.auth.models import User
from rest_framework import serializers

from .errors import Errors
from .models import Household, Membership, SubTask, Task, Zone


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class HouseholdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Household
        fields = ["id", "name", "mode", "created_at"]
        read_only_fields = ["created_at"]


class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = ["id", "user", "household", "role", "is_away"]

    def validate_household(self, household):
        Errors.Membership.require_membership(self.context["request"].user, household)
        return household

    def validate(self, attrs):
        request = self.context["request"]
        if self.instance:
            household = self.instance.household
            if "role" in attrs and attrs["role"] != self.instance.role:
                Errors.Membership.require_admin_for_role_change(request.user, household)
            if "is_away" in attrs and request.user.id != self.instance.user_id:
                Errors.Membership.require_admin_for_away_change(request.user, household)
        return attrs


class ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        fields = ["id", "household", "name", "is_shared", "residents"]

    def validate_household(self, household):
        Errors.Membership.require_membership(self.context["request"].user, household)
        return household


class SubTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubTask
        fields = ["id", "task", "title", "is_completed"]

    def validate_task(self, task):
        Errors.Membership.require_membership(self.context["request"].user, task.zone.household)
        return task


class TaskSerializer(serializers.ModelSerializer):
    subtasks = SubTaskSerializer(many=True, read_only=True)
    is_overdue = serializers.ReadOnlyField()

    class Meta:
        model = Task
        fields = [
            "id", "zone", "title", "description", "assignee",
            "status", "blocked_reason", "requires_approval",
            "awaiting_approval", "is_recurring", "interval_days",
            "deadline", "weight", "created_at", "is_overdue", "subtasks",
        ]
        read_only_fields = [
            "status", "blocked_reason", "awaiting_approval",
            "assignee", "created_at",
        ]

    def validate_zone(self, zone):
        Errors.Membership.require_membership(self.context["request"].user, zone.household)
        return zone
