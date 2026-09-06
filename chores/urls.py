from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("households", views.HouseholdViewSet, basename="household")
router.register("memberships", views.MembershipViewSet, basename="membership")
router.register("zones", views.ZoneViewSet, basename="zone")
router.register("tasks", views.TaskViewSet, basename="task")
router.register("subtasks", views.SubTaskViewSet, basename="subtask")
router.register("users", views.UserViewSet, basename="user")

urlpatterns = router.urls + [
    path("me/", views.MeView.as_view(), name="me"),
]
