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

## In progress

- (nothing in progress — Phase 3 not yet started)

## Not started
- Phase 3 — Governance & permission rules
- Phase 4 — Task lifecycle mechanics
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
