from django.contrib import admin

from .models import Household, Membership, SubTask, Task, Zone


class SubTaskInline(admin.TabularInline):
    model = SubTask
    extra = 0


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ("name", "mode", "created_at")
    list_filter = ("mode",)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "household", "role", "is_away")
    list_filter = ("role", "is_away", "household")


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "household", "is_shared")
    list_filter = ("is_shared", "household")
    filter_horizontal = ("residents",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "zone", "assignee", "status", "awaiting_approval", "deadline", "is_recurring")
    list_filter = ("status", "is_recurring", "requires_approval", "awaiting_approval", "zone__household")
    inlines = [SubTaskInline]


@admin.register(SubTask)
class SubTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "task", "is_completed")
    list_filter = ("is_completed",)
