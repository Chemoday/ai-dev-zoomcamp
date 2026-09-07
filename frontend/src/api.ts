import type { Household, Me, Membership, Mode, Role, SubTask, Task, TaskInput, UserRef, Zone } from './types'

export class ApiError extends Error {
  constructor(public status: number, public detail: string, public data: unknown) {
    super(detail)
    this.name = 'ApiError'
  }
  /** 404 also means "exists but is not yours" — the API does not distinguish. */
  get isNotFound() { return this.status === 404 }
  get isForbidden() { return this.status === 403 }
}

let readToken: () => string | null = () => null
/** Called once at startup so api.ts never imports the auth store (no cycle). */
export function provideToken(fn: () => string | null) { readToken = fn }

function detailOf(data: unknown, status: number): string {
  if (data && typeof data === 'object') {
    const d = data as Record<string, unknown>
    if (typeof d.detail === 'string') return d.detail
    if (Array.isArray(d.non_field_errors) && typeof d.non_field_errors[0] === 'string') return d.non_field_errors[0]
    const first = Object.values(d).find(v => Array.isArray(v) && typeof v[0] === 'string') as string[] | undefined
    if (first) return first[0]
  }
  return status === 0 ? 'Could not reach the server.' : `Request failed (${status}).`
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const token = readToken()
  if (token) headers.Authorization = `Token ${token}`
  let res: Response
  try {
    res = await fetch(path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) })
  } catch {
    throw new ApiError(0, 'Could not reach the server. Is Django running?', null)
  }
  if (res.status === 204) return undefined as T
  const data = await res.json().catch(() => null)
  if (!res.ok) throw new ApiError(res.status, detailOf(data, res.status), data)
  return data as T
}

const crud = <T, C = Partial<T>>(collection: string) => ({
  list: (query?: Record<string, string | number | undefined>) => {
    const qs = new URLSearchParams()
    Object.entries(query ?? {}).forEach(([k, v]) => { if (v !== undefined && v !== '') qs.set(k, String(v)) })
    const suffix = qs.toString() ? `?${qs}` : ''
    return request<T[]>('GET', `/api/${collection}/${suffix}`)
  },
  get: (id: number) => request<T>('GET', `/api/${collection}/${id}/`),
  create: (payload: C) => request<T>('POST', `/api/${collection}/`, payload),
  update: (id: number, payload: C) => request<T>('PATCH', `/api/${collection}/${id}/`, payload),
  remove: (id: number) => request<void>('DELETE', `/api/${collection}/${id}/`),
})

const action = (id: number, verb: string, body?: unknown) =>
  request<Task>('POST', `/api/tasks/${id}/${verb}/`, body)

export const api = {
  login: (username: string, password: string) => request<{ token: string }>('POST', '/api/token/', { username, password }),
  /** Needs the /api/me/ route — see frontend/README.md, "Backend prerequisites". */
  me: () => request<Me>('GET', '/api/me/'),
  users: () => request<UserRef[]>('GET', '/api/users/'),

  households: crud<Household, { name: string; mode: Mode }>('households'),
  memberships: crud<Membership, { user?: number; household?: number; role?: Role; is_away?: boolean }>('memberships'),
  zones: crud<Zone, { household?: number; name?: string; is_shared?: boolean; residents?: number[] }>('zones'),
  subtasks: crud<SubTask, { task?: number; title?: string; is_completed?: boolean }>('subtasks'),

  tasks: {
    ...crud<Task, Partial<TaskInput>>('tasks'),
    /** TODO → IN_PROGRESS, assigned to the caller. 403 if the caller is away. */
    start: (id: number) => action(id, 'start'),
    /** IN_PROGRESS → TODO, assignee cleared. Assignee or admin. */
    drop: (id: number) => action(id, 'drop'),
    /** reason is required free text — 400 without it. */
    block: (id: number, reason: string) => action(id, 'block', { reason }),
    unblock: (id: number) => action(id, 'unblock'),
    /** → DONE, or awaiting_approval in a hierarchical household. Spawns the next occurrence when recurring. */
    complete: (id: number) => action(id, 'complete'),
    /** Admins only, and only while awaiting_approval. */
    approve: (id: number) => action(id, 'approve'),
  },
}
