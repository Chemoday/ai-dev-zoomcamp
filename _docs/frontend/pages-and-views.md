# Frontend Pages & Views Specification

## Purpose and how to use this document

This document describes every page/view the Shared Household Chores
Manager frontend needs, and exactly what data and actions each one is
built from. It exists to be handed to a design tool (the `design` skill /
Claude Design) as the input for producing UI mockups — it is a **content
and behavior spec**, not a visual one. It intentionally says nothing about
colors, typography, or layout aesthetics; those are the design phase's
job. What it *does* pin down, precisely, is: what data appears on each
screen, where that data comes from (down to the exact API field), what
actions a user can take, which endpoint each action calls, and how the
screen differs by role or household governance mode.

Everything below is grounded in the actual Django REST Framework API
already built and tested (`chores/models.py`, `chores/serializers.py`,
`chores/views.py`, `chores/urls.py`, all under `/api/`). Nothing here
describes a hoped-for future endpoint without saying so explicitly — see
"Known gaps and current looseness" for the handful of things the backend
doesn't do yet or doesn't restrict yet.

## Domain glossary

- **Household** — the top-level group (a family, a flat-share). Has a
  `mode`: `P2P` (peer-to-peer, everyone equal) or `HIERARCHICAL` (has
  Admins and Members).
- **Membership** — links a User to a Household with a `role` (`ADMIN` or
  `MEMBER`) and an `is_away` flag ("vacation mode" — excludes the person
  from new task assignment while set). Roles are **per household**, not
  global: the same person can be an Admin in one household and a plain
  Member in another.
- **Zone** — a physical area within a household (a room, a shared space).
  Has `is_shared` and a list of `residents` (Users) for private zones.
- **Task** — a chore, scoped to a Zone. Has a `status`
  (`TODO`/`IN_PROGRESS`/`BLOCKED`/`DONE`), an optional `assignee`, and
  flags for `requires_approval`, `is_recurring` (+`interval_days`),
  `weight` (a free-form effort/points number), and `deadline`.
- **SubTask** — a checklist item belonging to a Task (e.g. "Mirror",
  "Toilet", "Floor" under a "Clean bathroom" task).

## Backend contract the frontend must respect

These are load-bearing rules — get any of these wrong in the UI and it
will either show impossible states or call an endpoint that rejects the
request.

**Authentication.** `POST /api/token/` with `{username, password}` returns
`{"token": "..."}`. Every other request must carry
`Authorization: Token <token>`. There is **no signup endpoint** and **no
password-reset endpoint** — user accounts are created out-of-band (Django
admin) today. The login screen's copy needs to reflect that a user can't
self-register.

**Who am I.** `GET /api/me/` returns `{id, username, email}` for the
caller. There is no session concept beyond the token — "logging out" is a
frontend-only action (discard the stored token); the API has no
token-revocation endpoint.

**Household-scoped visibility.** Every list/detail endpoint
(`households`, `memberships`, `zones`, `tasks`, `subtasks`) is filtered to
rows reachable through the caller's own household memberships. Fetching
an object outside the caller's households returns **404, not 403** — the
frontend cannot distinguish "doesn't exist" from "exists but isn't
yours," and shouldn't try to.

**Resolving IDs to names.** `assignee` on Task, `user` on Membership, and
`residents` on Zone are all bare numeric IDs, not nested objects.
`GET /api/users/` returns `[{id, username}, ...]` for every user who
shares at least one household with the caller. The frontend should fetch
this once per session/household context and keep an `id -> username`
lookup map for rendering names anywhere a raw user ID appears. This
endpoint is intentionally minimal (no email/avatar) and does not include
users outside the caller's households.

**Governance mode changes behavior, not just labels.** In a `P2P`
household, a task's `requires_approval` flag is ignored — `complete`
always goes straight to `DONE`. In a `HIERARCHICAL` household, if
`requires_approval` is true, `complete` instead sets `awaiting_approval:
true` and leaves `status: IN_PROGRESS` until an Admin calls `approve`.
The UI must not assume "requires approval" always means "will pause for
approval" — it depends on the household's mode too.

**The Task status machine and who can drive it.** Fields `status`,
`blocked_reason`, `awaiting_approval`, and `assignee` are **read-only** on
`Task` — PATCH cannot change them directly. They only change via six
POST action endpoints:

| Endpoint | Valid from | Effect | Who may call it |
|---|---|---|---|
| `POST /tasks/{id}/start/` | `TODO` | assigns caller, → `IN_PROGRESS` | any household member not marked `is_away` |
| `POST /tasks/{id}/drop/` | `IN_PROGRESS` | clears assignee, → `TODO` | the assignee, or a household Admin |
| `POST /tasks/{id}/block/` `{reason}` | `TODO` or `IN_PROGRESS` | → `BLOCKED`, sets `blocked_reason` | the assignee (if any) or a household Admin; **any** member if the task has no assignee yet |
| `POST /tasks/{id}/unblock/` | `BLOCKED` | → `IN_PROGRESS` (if assignee) or `TODO` (if not) | same as block |
| `POST /tasks/{id}/complete/` | `IN_PROGRESS` | → `DONE`, or → `awaiting_approval: true` if Hierarchical + `requires_approval` | the assignee, or a household Admin |
| `POST /tasks/{id}/approve/` | `awaiting_approval: true` | → `DONE` | a household Admin only |

Every one of these returns the updated Task on success (200) or
`{"detail": "<message>"}` on failure — `400` for an invalid transition or
a missing `reason`, `403` for "you're a household member but not allowed
to do this specific thing" (wrong actor, not an admin). A task outside
the caller's households is `404` before any of this even applies.
`blocked_reason` is **free text the caller supplies** — there is no fixed
list of reasons; a "block" form should just be a single required text
field.

**Recurring tasks regenerate silently.** If `is_recurring` is true and
`interval_days` is set, completing/approving a task creates a brand-new
sibling `Task` (same title/zone/etc., `status: TODO`, no assignee,
`deadline` pushed forward by `interval_days`). The action's response body
only contains the task that was just completed — the new occurrence isn't
linked to it anywhere in the API. To show "the next occurrence," the
frontend must re-fetch the task list and find it by zone/title, or simply
treat it as "a new card will appear on refresh."

**Subtasks are a plain checklist, not part of the state machine.**
Unlike Task's core fields, `SubTask.is_completed` is directly writable via
PATCH by any household member — no lifecycle gating. Checking a subtask
box should be a simple, immediate PATCH, not a POST action.

**No server-side filtering yet.** `GET /api/tasks/`, `/api/zones/`, etc.
return everything the caller can see across *all* their households, with
no `?household=`/`?zone=`/`?assignee=` query parameters supported. Any
"show me only this household's tasks" or "only tasks assigned to me"
view is a **client-side filter** over the full list today.

## Known gaps and current looseness (be aware, don't design around silently)

- **No signup, no password reset, no way to invite a new person by
  email.** Adding someone to a household means they must already have a
  Django user account. The "Add Member" flow can only pick from existing
  users — realistically, from `GET /api/users/`, which itself only
  returns people who already share a household with you, so it can't
  even help you find a *brand-new* person to add. For now, an "Add
  Member" screen needs an explicit "enter their username" text field
  (the backend will accept any valid user ID once it's known via a
  successful `POST /api/memberships/` — the frontend just has no lookup
  UI better than "ask the admin who created the accounts").
- **Membership creation isn't role-gated.** `POST /api/memberships/`
  only checks that the *requester* already belongs to the household —
  it does not require the requester to be an Admin, and does not stop
  them from creating the new membership with `role: "ADMIN"` directly.
  (Role *changes* on an existing membership *are* Admin-gated — this gap
  is specific to creation.) Design the "Add Member" screen assuming any
  member can currently do this; flagged here as a real permission hole
  worth tightening in the backend later, not something to paper over in
  the UI.
- **Household and Zone edits aren't Admin-gated either.** Any member of
  a household can rename it, change its `mode` (P2P ⇄ Hierarchical), or
  edit/delete any Zone. Only Task's lifecycle actions and the
  approve-only-by-Admin rule are actually enforced today.
- **No activity log / notifications.** There's no "who did what when"
  feed. A dashboard "recent activity" widget isn't buildable from the
  current API.

## Information architecture (sitemap)

```
Login
  └─ My Households  (list; empty state → prominent "Create household")
       ├─ Create Household
       └─ Household Dashboard  (per selected household)
            ├─ Zones
            │    └─ Zone Detail  (tasks filtered to this zone)
            ├─ Task Board  (all zones, filterable)
            │    ├─ Task Detail
            │    └─ New Task
            ├─ Approval Queue   (Hierarchical + Admin only)
            ├─ Members
            │    ├─ Add Member
            │    └─ Member Detail
            └─ Household Settings
       Profile  (own away toggle, list of my memberships across households)
```

A persistent top-level nav needs: current household name + a switcher
(if the user belongs to more than one), and a link to Profile. The
Approval Queue link should only render for Admins of a Hierarchical
household — it's meaningless otherwise (P2P never sets
`awaiting_approval`, and a plain Member can't call `approve` anyway).

## Page-by-page specifications

### 1. Login

- **API**: `POST /api/token/`.
- **Goal**: authenticate and store the token for subsequent requests.
- **Content**: username field, password field, submit button.
- **Error state**: on `400` with `non_field_errors`, show "Unable to log
  in with the provided credentials."
- **Copy note**: no "forgot password" or "sign up" links exist to wire up
  — if shown at all, they should read as "contact your household admin"
  rather than linking to a nonexistent flow.
- **On success**: fetch `GET /api/me/`, store `{id, username}` alongside
  the token, then load My Households.

### 2. My Households

- **API**: `GET /api/households/`.
- **Goal**: pick which household to work in, or create the first one.
- **Content**: one card/row per household — `name`, a mode badge
  (`P2P`/`Hierarchical`). Member count isn't available without an extra
  per-household `memberships` fetch; treat as optional/secondary info if
  shown at all, computed by filtering the memberships list once loaded.
- **Actions**: click a household → Household Dashboard. "+ Create
  household" → Create Household screen.
- **Empty state**: no households yet — this is the *only* screen a
  brand-new user lands on, so the empty state needs to be a clear,
  prominent call to create one (there's nothing else for them to do).

### 3. Create Household

- **API**: `POST /api/households/ {name, mode}`.
- **Content**: name text field, mode selector (`P2P` / `Hierarchical`)
  with a short explanation of what each means (equal permissions vs.
  admin-approval workflow).
- **On success**: the creator is automatically made an Admin member of
  the new household (backend does this atomically) — no separate "you're
  now the admin" step needed, just navigate straight to its Dashboard.

### 4. Household Dashboard

- **API**: `GET /api/memberships/` (find the caller's own row for this
  household to get their role), `GET /api/tasks/` (filtered client-side
  to this household's zones), `GET /api/zones/` (filtered client-side).
- **Goal**: orientation — what needs attention in this household right
  now.
- **Content**: household name + mode badge; the caller's own role badge;
  summary tiles: total open tasks, overdue count (`Task.is_overdue`),
  blocked count, and — **Admin + Hierarchical only** — a tile for tasks
  `awaiting_approval`, linking to the Approval Queue.
- **Actions**: nav links into Zones, Task Board, Members, Household
  Settings, and (conditionally) Approval Queue.
- **Empty state**: a new household has no zones/tasks yet — lead with
  "Add your first zone" rather than an empty task board.

### 5. Zones (list)

- **API**: `GET /api/zones/` (client-filtered to the current household),
  `POST /api/zones/` to create.
- **Content per zone**: `name`, `is_shared` badge, resident names
  (resolve `residents` IDs via the `/api/users/` lookup map), and a task
  count (client-computed from the tasks list filtered to this zone).
- **Actions**: "+ Add zone" opens a form (`name`, `is_shared` toggle,
  resident picker sourced from `/api/users/`). Click a zone → Zone
  Detail.

### 6. Zone Detail

- **API**: `GET /api/zones/{id}/`, `GET /api/tasks/` filtered
  client-side to `zone == id`.
- **Content**: zone name, `is_shared`, resident list (names via the
  lookup map), and the list of tasks in this zone (same task-card
  component as the Task Board, just pre-filtered).
- **Actions**: "+ New task" (pre-fills `zone`), edit zone
  (`PATCH /api/zones/{id}/`), delete zone.

### 7. Task Board

- **API**: `GET /api/tasks/`, client-filtered/grouped by `status` for a
  kanban layout, or shown as a flat filterable list — either is
  reasonable; server gives no preference since there's no query-param
  filtering to lean on either way.
- **Content per task card**: `title`, zone name, assignee name (or
  "Unassigned"), status badge, overdue indicator (if `is_overdue`),
  recurring icon (if `is_recurring`), blocked-reason snippet (if
  `BLOCKED`), awaiting-approval indicator (if set).
- **Filters** (all client-side): by zone, by assignee ("mine" using the
  stored `me.id`), by status.
- **Actions**: click a card → Task Detail. "+ New Task" → New Task form.
- **Empty state**: no tasks in this household yet.

### 8. Task Detail

- **API**: `GET /api/tasks/{id}/`, plus whichever of the six lifecycle
  actions applies.
- **Content**: full task fields, subtask checklist (`subtasks`, each with
  an inline checkbox that PATCHes `is_completed` directly — no
  confirmation needed, it's not state-machine-gated), and — if
  `BLOCKED` — the `blocked_reason` text prominently displayed.
- **Actions, conditionally rendered by current `status` and the viewer's
  relationship to the task** (assignee vs. not, Admin vs. not — the
  frontend doesn't need to pre-compute permission client-side beyond
  hiding obviously-inapplicable buttons; the API is the source of truth
  and will 400/403 either way):
  - `TODO` → show "Start" (and "Block" if the viewer is any household
    member, since an unassigned task can be blocked by anyone).
  - `IN_PROGRESS` → show "Drop", "Block", "Complete" (assignee or Admin).
  - `BLOCKED` → show "Unblock" (reopens a reason-entry-free form; the
    existing `blocked_reason` is just cleared).
  - `awaiting_approval: true` → show "Approve" **only if the viewer is a
    household Admin**; otherwise show a read-only "Awaiting admin
    approval" banner.
  - `DONE` → no actions; if `is_recurring`, a note that a new occurrence
    was created (link to Task Board, not to a specific task — there's no
    direct link available, see the gaps section above).
- **Error handling**: any 400/403 from an action should surface the
  `detail` message from the response directly — the backend's messages
  (e.g. "A reason is required to block a task", "Task is not awaiting
  approval") are already user-appropriate.

### 9. New Task / Edit Task form

- **API**: `POST /api/tasks/` (create) — `PATCH /api/tasks/{id}/` only
  covers the writable fields (edit is limited to metadata, not state —
  see the read-only fields list above).
- **Fields**: zone (picker, scoped to the current household's zones),
  title, description, `requires_approval` toggle (with a note that it
  only takes effect in Hierarchical households), `is_recurring` toggle +
  `interval_days` (shown only when recurring is on), `deadline`
  (datetime picker), `weight` (number, described as an optional
  effort/points value).
- Editing an existing task cannot touch `status`/`assignee`/
  `blocked_reason`/`awaiting_approval` — those fields shouldn't appear as
  editable inputs on this form at all, only on Task Detail via the
  lifecycle buttons.

### 10. Approval Queue

- **Visibility**: only shown/reachable for a household in `HIERARCHICAL`
  mode, to a viewer who is an Admin there (a Member has no `approve`
  capability and would just get 403s).
- **API**: `GET /api/tasks/` client-filtered to
  `awaiting_approval === true` within this household.
- **Content**: one row per pending task — title, assignee name, zone,
  when it was marked complete (not directly available — there's no
  timestamp for the completion event, only `Task.created_at` for the
  task itself; omit or note as unavailable rather than fabricating it).
- **Actions**: "Approve" per row (`POST /api/tasks/{id}/approve/`).
- **Empty state**: "Nothing waiting on your approval."

### 11. Members (list)

- **API**: `GET /api/memberships/` (client-filtered to the current
  household).
- **Content per row**: username (via `/api/users/` lookup), role badge,
  away-status badge (if `is_away`).
- **Actions**: "+ Add member" → Add Member form. Click a row → Member
  Detail.

### 12. Add Member

- **API**: `POST /api/memberships/ {user, household, role}`.
- **Content**: a text input for the user to add (see the gap noted above
  — there is no search/autocomplete against the full user directory,
  only against people already in a shared household, which is circular
  for a genuinely new person). Role selector (`ADMIN`/`MEMBER`).
- **Caveat surfaced in-UI**: since creation isn't Admin-gated on the
  backend today, don't hide this screen behind an "Admin only" client
  check that the API doesn't actually enforce — that would be UI-only
  security theater. It's fine to still default-hide the entry point
  behind "household settings" for a cleaner Member-facing UI, just don't
  present it as an enforced restriction.

### 13. Member Detail

- **API**: `PATCH /api/memberships/{id}/ {role}` or `{is_away}`,
  `DELETE /api/memberships/{id}/` (remove from household).
- **Content**: username, role, away toggle.
- **Role change**: only succeeds if the viewer is an Admin of this
  household — a Member attempting it gets a validation error
  ("Only an admin can change a member's role.").
- **Away toggle**: a user can always toggle their own; toggling someone
  else's requires the viewer to be an Admin ("You can only change your
  own away status.").

### 14. Household Settings

- **API**: `PATCH /api/households/{id}/ {name, mode}`,
  `DELETE /api/households/{id}/`.
- **Content**: name field, mode selector.
- **Caveat**: same as Add Member — this isn't currently Admin-gated by
  the backend, so treat any client-side "Admin only" gating here as a UX
  simplification, not a real security boundary.

### 15. Profile

- **API**: `GET /api/me/`, `GET /api/memberships/` (all of the caller's
  own rows, across every household they belong to — the endpoint
  already returns exactly this: everything reachable through their
  memberships includes their own rows).
- **Content**: username, email; a list of "my households" with role +
  away badge per one; a per-household away toggle
  (`PATCH /api/memberships/{id}/ {is_away: true/false}` on their own
  membership row — always allowed for oneself).
- No global "delete my account" or "change password" — neither exists in
  the API.

## Shared components

- **Task card** — title, zone name, assignee name/"Unassigned", status
  badge, overdue flag, recurring icon, blocked-reason snippet, approval
  indicator. Reused on Task Board, Zone Detail, and Approval Queue
  (subset of fields).
- **Status badge** — `TODO` / `IN_PROGRESS` / `BLOCKED` / `DONE`, four
  distinct visual states.
- **Role badge** — `ADMIN` / `MEMBER`, per household (never shown without
  also showing which household it applies to, since it's not global).
- **Mode badge** — `P2P` / `Hierarchical` on a household.
- **Approval banner** — "Awaiting admin approval" state on a task, with
  an Approve button only for Admins.
- **Subtask checklist** — a list of checkboxes, each an independent
  immediate PATCH.
- **User display** — resolves a raw user ID to a username via the
  `/api/users/` lookup map; falls back to "Unknown user" if the ID isn't
  in the map (shouldn't happen given the API's own scoping, but a
  reasonable defensive default for a lookup built from a separate
  request).

## Open questions left for the design phase

These are genuinely open — visual/interaction decisions, not backend
constraints:

- Task Board as a kanban (columns per status) vs. a flat filterable list.
- Whether "my tasks" is a filter within the Task Board or its own
  dedicated view.
- How prominently to surface the "membership creation isn't role-gated"
  and "household edits aren't role-gated" looseness in the UI copy, if
  at all, versus treating it purely as a backend concern to fix later.
- Mobile-first vs. desktop-first layout priority (a chores app is
  plausibly checked most often from a phone, but this hasn't been
  decided).
