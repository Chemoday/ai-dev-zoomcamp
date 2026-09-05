# 🧹 Shared Household Chores Manager (Backend)

A Django-based backend service designed to manage shared household chores and responsibilities. Built to support dormitories, student shared flats, and family apartments through a flexible space-zoning and governance model.

---

## 🎯 Core Concepts

The system is designed around three main layers of abstraction:
1. **Household** — The top-level living unit configured with a specific governance mode.
2. **Zones** — Spatial areas categorized into private rooms (linked to specific residents) and common areas (kitchen, bathroom, hallway).
3. **Tasks** — Actionable chores linked to zones, featuring checklists (subtasks) and deadlines.

---

## ⚙️ Key MVP Features

### 1. Governance Modes
* **Peer-to-Peer (P2P):** All flatmates have equal permissions. Any resident can propose tasks that become immediately actionable (tailored for roommates/students).
* **Hierarchical:** Structured roles with Admins (parents/head tenants) and Members (kids/residents). Tasks and completions can require admin approval.

### 2. Task Mechanics & Lifecycle
* **One-off & Recurring:** Supports both single ad-hoc tasks and periodic routines (with custom day intervals).
* **Checklists (Subtasks):** Break down complex chores into concrete checklist items (e.g., *Mirror*, *Toilet*, *Floor*).
* **Flexible Completion:** Configurable verification flow per task — instant trust-based completion or requiring verification from an Admin.

### 3. Real-Life Living Scenarios
* **Drop / Can't Do:** Assignees can release an accepted task; it returns to the unassigned pool for anyone to claim.
* **Overdue Tracking:** Tasks past their deadline are flagged, remaining visible to the whole household so others can step in.
* **Blocked State (`BLOCKED`):** Temporarily flag a chore as unfeasible with a reason (e.g., *"No hot water"* or *"Need vacuum bags"*).
* **Vacation Mode (`is_away`):** Residents can toggle away status to temporarily pause chore rotations while on holiday or sick leave.

---

## 🏛 Domain Data Models (Django ORM)

```text
User (Django Auth)
  │
  ├── Membership ── Household (mode: P2P | HIERARCHICAL)
  │     ├── role: ADMIN | MEMBER
  │     └── is_away: Boolean
  │
  ├── Zone (is_shared: Boolean, residents: M2M to User)
  │
  └── Task
        ├── zone: FK(Zone)
        ├── assignee: FK(User, nullable)
        ├── status: TODO | IN_PROGRESS | BLOCKED | DONE
        ├── requires_approval: Boolean
        ├── is_recurring: Boolean (interval_days)
        ├── deadline: DateTime
        ├── weight: Integer (extensibility hook for points/karma)
        │
        └── SubTask (task: FK, title, is_completed: Boolean)