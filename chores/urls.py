from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("households", views.HouseholdViewSet, basename="household")
router.register("memberships", views.MembershipViewSet, basename="membership")
router.register("zones", views.ZoneViewSet, basename="zone")
router.register("tasks", views.TaskViewSet, basename="task")
router.register("subtasks", views.SubTaskViewSet, basename="subtask")

urlpatterns = router.urls
