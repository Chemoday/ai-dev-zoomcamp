export type Mode = 'P2P' | 'HIERARCHICAL'
export type Role = 'ADMIN' | 'MEMBER'
export type TaskStatus = 'TODO' | 'IN_PROGRESS' | 'BLOCKED' | 'DONE'

export interface Me { id: number; username: string; email: string }
/** GET /api/users/ — every user sharing at least one household with the caller. */
export interface UserRef { id: number; username: string }

export interface Household { id: number; name: string; mode: Mode; readonly created_at: string }
export interface Membership { id: number; user: number; household: number; role: Role; is_away: boolean }
export interface Zone { id: number; household: number; name: string; is_shared: boolean; residents: number[] }
export interface SubTask { id: number; task: number; title: string; is_completed: boolean }

/**
 * Fields marked readonly are read_only_fields on TaskSerializer: PATCH cannot
 * change them. They move only through the six lifecycle actions in api.tasks.
 */
export interface Task {
  readonly id: number
  zone: number
  title: string
  description: string
  requires_approval: boolean
  is_recurring: boolean
  interval_days: number | null
  deadline: string | null
  weight: number
  readonly status: TaskStatus
  readonly assignee: number | null
  readonly blocked_reason: string
  readonly awaiting_approval: boolean
  readonly created_at: string
  readonly is_overdue: boolean
  readonly subtasks: SubTask[]
}

/** Exactly what POST /api/tasks/ and PATCH /api/tasks/{id}/ accept. */
export type TaskInput = Pick<
  Task,
  'zone' | 'title' | 'description' | 'requires_approval' | 'is_recurring' | 'interval_days' | 'deadline' | 'weight'
>

export const STATUS_LABEL: Record<TaskStatus, string> = {
  TODO: 'To do', IN_PROGRESS: 'In progress', BLOCKED: 'Blocked', DONE: 'Done',
}
export const MODE_LABEL: Record<Mode, string> = { P2P: 'Peer-to-peer', HIERARCHICAL: 'Hierarchical' }
export const ROLE_LABEL: Record<Role, string> = { ADMIN: 'Admin', MEMBER: 'Member' }
