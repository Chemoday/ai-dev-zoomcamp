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

## In progress

- (nothing in progress — Phase 5 not yet started)

## Not started
- Phase 5 — Interface layer (pending open decision)
- Phase 6 — Auth (pending open decision)
- Phase 7 — Tests
- Phase 8 — Stretch: CI & deployment

## Notes / gotchas for future sessions

- `uv` is on PATH via `~/.profile` (login shells) but NOT `~/.bashrc`
  (non-login interactive shells). In Claude Code's Bash tool, prefix
  commands with `export PATH="$HOME/.local/bin:$PATH"` if `uv` isn't
  found.
- Nothing has been committed for the Django app yet as of this entry.
