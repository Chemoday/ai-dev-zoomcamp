import functools

from django.contrib.auth.models import User
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from . import lifecycle, permissions
from .models import Household, Membership, SubTask, Task, Zone
from .serializers import (
    HouseholdSerializer,
    MembershipSerializer,
    SubTaskSerializer,
    TaskSerializer,
    UserSerializer,
    ZoneSerializer,
)


class MeView(APIView):
    def get(self, request):
        user = request.user
        return Response({"id": user.id, "username": user.username, "email": user.email})


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSerializer

    def get_queryset(self):
        household_ids = Membership.objects.filter(
            user=self.request.user
        ).values_list("household_id", flat=True)
        co_member_ids = Membership.objects.filter(
            household_id__in=household_ids
        ).values_list("user_id", flat=True)
        return User.objects.filter(id__in=co_member_ids)


class HouseholdScopedMixin:
    """Restricts a viewset's queryset to rows reachable through the
    requester's own household memberships, via `household_lookup` — a
    field-lookup path relative to the model (e.g. "zone__household_id").
    """

    household_lookup = "household_id"

    def get_queryset(self):
        household_ids = Membership.objects.filter(
            user=self.request.user
        ).values_list("household_id", flat=True)
        return super().get_queryset().filter(**{f"{self.household_lookup}__in": household_ids})


class HouseholdViewSet(HouseholdScopedMixin, viewsets.ModelViewSet):
    queryset = Household.objects.all()
    serializer_class = HouseholdSerializer
    household_lookup = "id"

    def perform_create(self, serializer):
        household = serializer.save()
        Membership.objects.create(
            user=self.request.user, household=household, role=Membership.Role.ADMIN
        )


class MembershipViewSet(HouseholdScopedMixin, viewsets.ModelViewSet):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer


class ZoneViewSet(HouseholdScopedMixin, viewsets.ModelViewSet):
    queryset = Zone.objects.all()
    serializer_class = ZoneSerializer


class SubTaskViewSet(HouseholdScopedMixin, viewsets.ModelViewSet):
    queryset = SubTask.objects.all()
    serializer_class = SubTaskSerializer
    household_lookup = "task__zone__household_id"


def _lifecycle_action(handler):
    """Fetch the task, run `handler`, and translate lifecycle/permission
    errors into DRF responses — keeps each action body to a single call
    into `lifecycle.py`.
    """

    @functools.wraps(handler)
    def wrapper(self, request, pk=None):
        task = self.get_object()
        try:
            handler(self, request, task)
        except (lifecycle.InvalidTransition, ValueError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except permissions.PermissionDenied as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        return Response(TaskSerializer(task).data)

    return wrapper


class TaskViewSet(HouseholdScopedMixin, viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    household_lookup = "zone__household_id"

    @action(detail=True, methods=["post"])
    @_lifecycle_action
    def start(self, request, task):
        lifecycle.start_task(task, request.user)

    @action(detail=True, methods=["post"])
    @_lifecycle_action
    def drop(self, request, task):
        lifecycle.drop_task(task, request.user)

    @action(detail=True, methods=["post"])
    @_lifecycle_action
    def block(self, request, task):
        lifecycle.block_task(task, request.user, request.data.get("reason", ""))

    @action(detail=True, methods=["post"])
    @_lifecycle_action
    def unblock(self, request, task):
        lifecycle.unblock_task(task, request.user)

    @action(detail=True, methods=["post"])
    @_lifecycle_action
    def complete(self, request, task):
        lifecycle.complete_task(task, request.user)

    @action(detail=True, methods=["post"])
    @_lifecycle_action
    def approve(self, request, task):
        lifecycle.approve_task(task, request.user)
