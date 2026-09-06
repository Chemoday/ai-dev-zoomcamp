# Implementation Plan — Shared Household Chores Manager

Source spec: `README.md` (project root). Built for Homework 1 of the
AI Dev Tools Zoomcamp — scope is a working Django backend covering the
MVP features in the spec, with tests. This plan feeds into `backlog.md`
(a later, more granular task list), so it stays at the phase/decision
level rather than listing every line of code.

## Tech stack

- **Language/runtime**: Python, managed with `uv` (`uv init`, `uv add`,
  `uv run ...`) instead of pip/venv directly.
- **Framework**: Django, single project with one app (name TBD when
  scaffolding — e.g. `chores`).
- **Database**: SQLite for now (per project decision) — zero setup,
  fine for MVP and tests. Revisit only if concurrent-write behavior
  needs real testing.
- **Interface layer**: not yet decided — see "Open decisions" below.
- **Tests**: Django's built-in test runner (`uv run python manage.py
  test`) unless a later phase adopts `pytest-django`.

## Open decisions (resolve before/while building the relevant phase)

1. **API vs templates vs admin-only** — Resolved: DRF API, deferred.
   Django admin remains the only interface for now (models + admin
   registration from Phase 2); Phase 5 will add DRF serializers/viewsets
   when picked back up. Note: editing `Task.status` directly in the
   admin bypasses `chores/lifecycle.py` (no approval gating, no
   recurring regeneration) — acceptable for now, but worth adding
   custom admin actions wired to `lifecycle.py` if the admin ends up
   being used as more than a quick data-inspection tool before DRF
   lands.
2. **Auth** — Resolved: DRF `TokenAuthentication` (not JWT/Basic) —
   simplest fit for project scope, no expiry/refresh complexity needed.
   Implemented in Phase 6. Django's built-in `User` model is used
   regardless.
3. **Deployment target** — GitHub hosts the code, not a running Django
   process (GitHub Pages is static-only). If/when deployment is
   wanted, pick a host (Render/Railway/Fly.io free tier are common
   fits) — separate from this homework's scope.

## Phase 0 — Tooling setup

- Initialize `uv` project (`pyproject.toml`, lockfile).
- Add Django as a dependency via `uv add django`.
- Confirm `.gitignore` covers Python/Django/uv artifacts
  (`__pycache__/`, `*.pyc`, `.venv/`, `db.sqlite3`, `.env`).

## Phase 1 — Django project & app scaffolding

- `uv run django-admin startproject <project_name> .`
- `uv run python manage.py startapp <app_name>`
- Register the app in `INSTALLED_APPS`.
- Run initial migration, create a superuser, confirm
  `uv run python manage.py runserver` boots.

## Phase 2 — Core domain models

Implement the ORM structure from README as Django models:

- `Household` (governance `mode`: P2P | HIERARCHICAL)
- `Membership` (User ↔ Household, `role`: ADMIN | MEMBER, `is_away`)
- `Zone` (`is_shared`, M2M residents)
- `Task` (zone FK, assignee FK nullable, `status`, `requires_approval`,
  `is_recurring`/`interval_days`, `deadline`, `weight`)
- `SubTask` (task FK, `title`, `is_completed`)

Register all models in Django admin so the app is inspectable/usable
before any custom views exist. Migrate.

## Phase 3 — Governance & permission rules

- Enforce P2P vs Hierarchical differences: in P2P, any member can
  propose/actionable a task immediately; in Hierarchical, admin
  approval gates apply.
- Role checks (Admin/Member) for actions that require them.
- `is_away` toggling should exclude a member from new task assignment
  while set.

## Phase 4 — Task lifecycle mechanics

- Status transitions: `TODO → IN_PROGRESS → DONE`, plus `BLOCKED`.
- Recurring task regeneration based on `interval_days`.
- Drop/"can't do": unassign and return task to the shared pool.
- Overdue detection (deadline passed, still not `DONE`) — visible
  household-wide.
- `BLOCKED` state requires a reason string.
- Verification flow: instant-complete vs admin-approval, driven by
  `requires_approval`.

## Phase 5 — Interface layer — Done

DRF serializers (`chores/serializers.py`) + `ModelViewSet`s
(`chores/views.py`) for all 5 models, routed under `/api/` via
`chores/urls.py` + a `DefaultRouter`. Task lifecycle actions exposed as
`@action` endpoints (`start`/`drop`/`block`/`unblock`/`complete`/`approve`)
that delegate to `chores/lifecycle.py` — views contain no
authorization/state-machine logic of their own. Querysets scoped to the
requesting user's households (`Membership` lookup); an object outside the
caller's households returns 404, not 403. `Task` fields that only change
via lifecycle actions (`status`, `blocked_reason`, `awaiting_approval`,
`assignee`) are read-only on the serializer.

As part of this, closed a previously-deferred gap: `lifecycle.drop_task`/
`block_task`/`unblock_task` took no caller identity, and `complete_task`'s
`actor` param was unused. Added `permissions.can_manage_task(user, task)`
(assignee or admin may act on a claimed task; any member may act on an
unclaimed one) and now enforce it first in all four functions.

## Phase 6 — Auth — Done

DRF `TokenAuthentication` (`rest_framework.authtoken`) + `SessionAuthentication`
(dev/browsable-API only). Login via `POST /api/token/` (DRF's built-in
`obtain_auth_token`) → `{"token": "..."}`; clients send
`Authorization: Token <token>`. Global default permission class is
`IsAuthenticated`.

## Phase 7 — Tests

- Model-level unit tests: status transitions, recurring task
  generation, overdue calculation, subtask completion.
- Governance/permission tests: P2P vs Hierarchical behavior, admin
  approval gating.
- Interface-level tests once Phase 5 lands (view/API tests).
- Run via `uv run python manage.py test`.

## Phase 8 — Stretch: CI & deployment (out of scope for Homework 1)

- GitHub Actions workflow: run `uv run python manage.py test` on push.
- Dockerfile for containerized runs.
- Pick and configure an actual hosting target (see Open Decision #3).
