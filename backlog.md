# Backlog

Derived from `_docs/plan.md`. Written retrospectively after Phases 0-3
were already implemented — those tasks are marked done below rather
than re-planned. See `_docs/progress.md` for the detailed log.

1. **Set up the `uv`-managed Python project and add Django as a
   dependency.** — ✅ Done
2. **Scaffold the Django project (`config`) and the `chores` app;
   register the app in `INSTALLED_APPS`.** — ✅ Done
3. **Implement the core domain models** (`Household`, `Membership`,
   `Zone`, `Task`, `SubTask`) per the README data model, register them
   in Django admin, and run the initial migration. — ✅ Done
4. **Implement governance & permission rules**: admin/member role
   checks, P2P vs Hierarchical approval gating, and `is_away`-based
   exclusion from task assignment (`chores/permissions.py`). — ✅ Done
5. **Implement task lifecycle mechanics**: status transitions
   (`TODO`/`IN_PROGRESS`/`BLOCKED`/`DONE`), drop/"can't do" (unassign
   back to the pool), overdue detection, `BLOCKED` state with a
   required reason, recurring task regeneration (`interval_days`), and
   the completion/approval flow (using
   `permissions.task_requires_admin_approval`). — ✅ Done
6. **Decide and implement the interface layer** — Django admin only,
   server-rendered views, or a DRF API — for the actions in task 5. —
   ✅ Done (DRF API: serializers + viewsets under `/api/`, see
   `chores/serializers.py`/`views.py`/`urls.py`)
7. **Decide and implement authentication** for whatever interface layer
   task 6 lands on (Django's built-in auth already backs the admin). —
   ✅ Done (DRF `TokenAuthentication`, login via `POST /api/token/`)
8. **Write the test suite**: model-level tests (status transitions,
   recurring generation, overdue calculation), governance/permission
   tests (P2P vs Hierarchical, admin approval gating), and
   interface-level tests once task 6 lands. Run via
   `uv run python manage.py test`. — ✅ Done (58 tests total, including
   `chores/test_api.py` for the interface layer)
9. **(Stretch) CI & deployment**: GitHub Actions workflow to run tests
   on push, a Dockerfile, and picking an actual hosting target (GitHub
   itself only hosts the code, not a running Django process). — Not
   started
