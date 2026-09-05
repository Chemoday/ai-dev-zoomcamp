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

## Not started
- Phase 5 — Interface layer (pending open decision)
- Phase 6 — Auth (pending open decision)
- Phase 8 — Stretch: CI & deployment

## Notes / gotchas for future sessions

- `uv` is on PATH via `~/.profile` (login shells) but NOT `~/.bashrc`
  (non-login interactive shells). In Claude Code's Bash tool, prefix
  commands with `export PATH="$HOME/.local/bin:$PATH"` if `uv` isn't
  found.
