# Progress Log

Tracks what's actually been done against `_docs/plan.md`, so work isn't
lost across sessions/context resets. Update this after each meaningful
step — append, don't rewrite history.

## Done

- Repo initialized locally, remote `origin` → `Chemoday/ai-dev-zoomcamp`,
  default branch `main`.
- Git auth wired via `$GITHUB_AI_DEV_ZOOMCAMP_TOKEN` + local credential
  helper (see `.claude/skills/ai-dev-zoomcamp-git-ops/SKILL.md`).
- `.gitignore`, `README.md`, `_docs/plan.md` committed and pushed.
- `ai-dev-zoomcamp-git-ops` Claude Code skill committed and pushed.
- `uv` installed (`~/.local/bin/uv`, v0.12.10).

- Phase 0 — `uv` project initialized (`--app` layout), Django added as a
  dependency (Django 6.1.1, Python 3.12.14, `.venv` created by `uv`).
- Phase 1 — Django project `config` + app `chores` scaffolded, `chores`
  registered in `INSTALLED_APPS` (`config/settings.py`), initial
  migrations applied (SQLite), dev server confirmed working by user,
  superuser created (username `chemoday`, local dev password only).

- Phase 2 — Models added in `chores/models.py` (Household, Membership,
  Zone, Task, SubTask) matching the README ORM diagram, plus `blocked_reason`
  on Task for the BLOCKED-state feature. All registered in
  `chores/admin.py`. Migration `chores/0001_initial.py` generated and
  applied. `manage.py check` passes.

- Phase 3 — `chores/permissions.py` added: `is_admin`/`require_admin`
  (role checks), `task_requires_admin_approval` (P2P ignores per-task
  `requires_approval`, Hierarchical honors it), `is_available_for_assignment`
  + `assign_task` (excludes `is_away` members). `Membership.is_admin`
  property added to the model (no migration needed — not a DB field).
  Manually smoke-tested via `manage.py shell`, not yet covered by
  `manage.py test` (deferred to Phase 7).

- Phase 4 — `chores/lifecycle.py` added: `start_task`/`drop_task`
  (assign/unassign pool cycle), `block_task`/`unblock_task` (required
  reason), `complete_task`/`approve_task` (uses
  `permissions.task_requires_admin_approval` to gate on `awaiting_approval`),
  recurring regeneration on completion (`interval_days`), and
  `Task.is_overdue` computed property. Added `Task.awaiting_approval`
  field + migration `0002_task_awaiting_approval`. Manually
  smoke-tested via `manage.py shell`, not yet covered by `manage.py
  test` (deferred to Phase 7).
- Backfilled `backlog.md` (repo root) retrospectively for Homework 1
  Question 4 — kept local/uncommitted per user request as of this entry.

- Phase 7 — `chores/tests.py`: 31 tests covering `Membership.is_admin`,
  `Task.is_overdue`, all of `chores/permissions.py`, and all of
  `chores/lifecycle.py` (start/drop, block/unblock, complete/approve
  gating, recurring regeneration). All passing via
  `uv run python manage.py test`. Done ahead of Phases 5-6 since those
  are blocked on open decisions and Homework 1's own flow goes straight
  from "implement a few backlog items" to "add tests."
- Reviewed the test suite for gaps (not just pass/fail); added 6 tests
  closing real holes: per-household scoping of `is_admin`/
  `is_available_for_assignment` (verified via mutation testing — briefly
  broke the household filter and confirmed these two tests catch it),
  `unblock_task`'s no-assignee branch, P2P ignoring `requires_approval`
  end-to-end through `complete_task`, `start_task` propagating
  `PermissionDenied` for an away user, recurring regeneration via the
  `approve_task` path, and `Membership`'s `unique_together` constraint.
  Open design question (not yet resolved): `complete_task` takes an
  unused `actor` param and `drop_task`/`block_task` take none at all —
  currently *any* user can complete/drop/block *any* task, with no
  authorization check. Deliberately not fixed yet — deferred until
  Phase 5/6 define how a caller's identity is actually supplied.

## In progress

- (nothing in progress)

- Phase 5/6 — DRF API + TokenAuthentication (2026-09-07). Added
  `djangorestframework` dependency; `rest_framework` +
  `rest_framework.authtoken` in `INSTALLED_APPS`; migrated (creates the
  authtoken table). Note: in the installed DRF version (3.18.0),
  `TokenAuthentication` lives at `rest_framework.authentication.
  TokenAuthentication`, not under `rest_framework.authtoken.authentication`
  — the latter path doesn't exist and raises an `ImportError` on
  `manage.py migrate`/`runserver`.
  - Closed the deferred authorization gap: added
    `permissions.can_manage_task(user, task)` (assignee or admin may act
    on a claimed task; any member may act on an unclaimed one) and wired
    it into `lifecycle.drop_task`/`block_task`/`unblock_task` (new
    required `actor` param — breaking signature change) and
    `complete_task` (previously-unused `actor` param now enforced).
    Existing `chores/tests.py` calls updated for the new signatures; 7
    new tests added to `LifecycleTests` covering non-assignee rejection
    and admin override for each of the four functions.
  - `chores/serializers.py` (new): one `ModelSerializer` per model.
    `Task.status`/`blocked_reason`/`awaiting_approval`/`assignee` are
    read-only (only change via lifecycle actions). `validate_<fk>`
    methods on Zone/Task/SubTask/Membership reject attaching to a
    household the requester isn't a member of.
    `MembershipSerializer.validate` requires admin for role changes or
    changing someone else's `is_away`.
  - `chores/views.py` (replaced stub): `ModelViewSet` per model,
    querysets scoped to the requester's households via a
    `_household_ids(user)` helper. `HouseholdViewSet.perform_create`
    auto-creates an ADMIN `Membership` for the creator.
    `TaskViewSet` adds `start`/`drop`/`block`/`unblock`/`complete`/
    `approve` `@action` endpoints, each delegating straight to
    `lifecycle.*` via a shared `_lifecycle_response` helper mapping
    `InvalidTransition`/`ValueError` → 400 and `PermissionDenied` → 403.
    An object outside the caller's households is 404 (queryset scoping),
    never 403.
  - `chores/urls.py` (new): `DefaultRouter` under `/api/`. `config/urls.py`
    wires it in plus `POST /api/token/` (DRF's `obtain_auth_token`).
  - `chores/test_api.py` (new): `APITestCase`-based — auth
    (401/token-success/token-failure), household scoping (list filtering,
    404 across households, creator-becomes-admin), and full task
    lifecycle via HTTP (start/drop/block/unblock/complete/approve happy
    paths, wrong-actor 403, wrong-state 400, P2P vs Hierarchical approval
    gating end-to-end).
  - All 58 tests pass (`uv run python manage.py test`). Manually
    smoke-tested the full happy path via `runserver` + `curl`: token →
    create household (creator auto-admin) → zone → task → start →
    complete → DONE; confirmed a user outside the household gets 404 on
    that task. Smoke-test users/data cleaned up afterward.
  - Style cleanup pass (same day, after user review request): replaced
    the 5 hand-written `get_queryset()`s + `_household_ids` helper in
    `chores/views.py` with a `HouseholdScopedMixin` (`household_lookup`
    class attr per viewset) plus `queryset = Model.objects.all()` on
    each viewset; replaced the lambda + `_lifecycle_response` pattern in
    `TaskViewSet`'s six lifecycle actions with a `_lifecycle_action`
    decorator, so each action body is a single call into `lifecycle.py`.
    Extracted a shared `_require_membership` helper in
    `chores/serializers.py` to de-duplicate the four `validate_<fk>`
    household-membership checks. Confirmed `Task.blocked_reason` was
    already a free-text `CharField` with no hardcoded choices (a chat
    misreading, not a real issue) — no change needed there. All 58 tests
    still pass after the refactor; re-smoke-tested start/block/complete
    via `runserver` + `curl` to confirm the decorator/mixin behave
    identically at runtime.

- Phase 8 (partial) — CI added: `.github/workflows/tests.yml` runs
  `uv run python manage.py test` on every push/PR to `main`, plus a
  status badge in `README.md`. Deployment target still not started.

- API additions for frontend readiness (2026-09-07): while drafting
  `_docs/frontend/pages-and-views.md`, found the API had no way to tell
  the frontend who is logged in, or to resolve `assignee`/`Membership.
  user`/`Zone.residents` IDs to display names. Added `GET /api/me/`
  (returns the caller's own id/username/email) and `GET /api/users/`
  (read-only, scoped to users who share a household with the caller,
  returns id/username only — not exposed for non-household-mates).
  2 new tests in `chores/test_api.py`; all 60 tests pass. Manually
  smoke-tested both via `runserver` + `curl`.

## Not started
- Deployment target (rest of Phase 8)

## Notes / gotchas for future sessions

- `uv` is on PATH via `~/.profile` (login shells) but NOT `~/.bashrc`
  (non-login interactive shells). In Claude Code's Bash tool, prefix
  commands with `export PATH="$HOME/.local/bin:$PATH"` if `uv` isn't
  found.
