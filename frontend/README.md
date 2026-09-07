# Chores frontend

Vue 3 + TypeScript + Vite, talking to the DRF API in this repo. Every component is
`<script setup lang="ts">`; every component stylesheet is `<style scoped>`. The two
global stylesheets are the design-system tokens (`src/styles/nocturne.css`) and
document-level resets (`src/styles/base.css`) — nothing else is global.

## Run it

    cd frontend
    npm install
    npm run dev          # http://localhost:5173, /api proxied to :8000

Vite proxies `/api` to `http://localhost:8000` (override with `DJANGO_ORIGIN`), so the
dev server is same-origin and **no CORS configuration is needed** — do not install
django-cors-headers for this.

    npm run typecheck    # vue-tsc, no emit
    npm run build        # dist/

## Backend prerequisites

**`/api/me/` and `/api/users/` already exist** (`chores/views.py`'s `MeView`/
`UserViewSet`, routed in `chores/urls.py`) — added in a prior session, ahead of this
scaffold. Verified working end-to-end through the Vite proxy.

One thing still missing: **query-parameter filtering.** `api.*.list()` already accepts a query object, and
`stores/household.ts` marks where to pass it. Until then every list arrives whole and
is narrowed client-side.

    # settings.py: INSTALLED_APPS += ["django_filters"]
    from django_filters.rest_framework import DjangoFilterBackend

    class TaskViewSet(HouseholdScopedMixin, viewsets.ModelViewSet):
        filter_backends = [DjangoFilterBackend]
        filterset_fields = ["zone", "zone__household", "assignee", "status", "awaiting_approval"]

## Serving the build from Django

History-mode routing needs a catch-all so `/h/1/tasks/4` survives a refresh.

    # config/settings.py
    TEMPLATES[0]["DIRS"] = [BASE_DIR / "frontend" / "dist"]
    STATICFILES_DIRS = [BASE_DIR / "frontend" / "dist" / "assets"]

    # config/urls.py — last pattern only, after admin/ and api/
    from django.views.generic import TemplateView
    urlpatterns += [re_path(r"^(?!api/|admin/|static/).*$", TemplateView.as_view(template_name="index.html"))]

## Shape of it

| Path | What it holds |
| --- | --- |
| `src/types.ts` | The API's models. Task's five `read_only_fields` are `readonly`, and `TaskInput` is the exact writable subset — a PATCH cannot carry `status` or `assignee` without a compile error. |
| `src/api.ts` | One typed client. `ApiError` carries `status` and the backend's own `detail` string. The six lifecycle actions are named methods, not a stringly-typed POST. |
| `src/stores/auth.ts` | Token (localStorage) + `me`. Sign-out discards the token; the API has no revocation. |
| `src/stores/household.ts` | The single cache of households/memberships/zones/tasks/users, with getters narrowing to the current household and `userName(id)` resolving ids to names. |
| `src/stores/ui.ts` | `error`/`notice`/`busy` and `run()`, which surfaces backend messages verbatim. |
| `src/composables/useTaskDisplay.ts` | Card/row display fields, and `availableActions()` — which lifecycle buttons apply. |
| `src/composables/useTaskActions.ts` | The six actions, each followed by a reload (recurring completion spawns a sibling the response never mentions). |
| `src/router/index.ts` | 15 routes, history mode. Guards handle auth, selecting the household from `:hid`, and keeping the approval queue to admins of hierarchical households. |

## Behaviour worth not breaking

- **Governance mode changes behaviour, not labels.** In P2P, `requires_approval` is
  ignored and `complete` goes straight to DONE. Only in hierarchical does it pause at
  `awaiting_approval`.
- **The task state machine is server-side.** `status`, `assignee`, `blocked_reason` and
  `awaiting_approval` move only through the six POST actions.
- **Subtasks are not gated.** `is_completed` is a plain PATCH by any member.
- **404 means "not yours" too.** The API does not distinguish missing from invisible.
- **Two screens claim no authority they have:** Add Member and Household Settings show a
  `PermissionWarning` because the backend does not admin-gate them.

## Not built

Signup, password reset, invite-by-email and any activity feed — no endpoints exist. The
"when was this completed" column in the approval queue is omitted rather than fabricated:
the API stores no completion timestamp.
