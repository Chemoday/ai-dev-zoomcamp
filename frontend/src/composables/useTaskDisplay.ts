import { useHouseholdStore } from '@/stores/household'
import { STATUS_LABEL, type Task, type TaskStatus } from '@/types'

const STATUS_TAG: Record<TaskStatus, string> = {
  TODO: 'tag tag-neutral',
  IN_PROGRESS: 'tag tag-accent',
  BLOCKED: 'tag tag-outline',
  DONE: 'tag tag-accent-2',
}

export function formatDeadline(value: string | null): string {
  if (!value) return 'No deadline'
  const d = new Date(value)
  const sameYear = d.getFullYear() === new Date().getFullYear()
  return `Due ${d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: sameYear ? undefined : 'numeric' })}`
}

/** Everything a task card or row shows, resolved from the store's lookups. */
export function useTaskDisplay() {
  const store = useHouseholdStore()
  return (task: Task) => ({
    task,
    zoneName: store.zoneName(task.zone),
    assigneeName: store.userName(task.assignee),
    statusLabel: STATUS_LABEL[task.status],
    statusClass: STATUS_TAG[task.status],
    deadlineLabel: formatDeadline(task.deadline),
    checklistLabel: task.subtasks.length
      ? `${task.subtasks.filter(s => s.is_completed).length} of ${task.subtasks.length} done`
      : '',
  })
}

/**
 * Which lifecycle buttons make sense for a task right now. The API is the real
 * gate (400/403); this only hides the obviously inapplicable.
 */
export function availableActions(task: Task, isAdmin: boolean) {
  if (task.awaiting_approval) return isAdmin ? (['approve'] as const) : ([] as const)
  if (task.status === 'TODO') return ['start', 'block'] as const
  if (task.status === 'IN_PROGRESS') return ['complete', 'drop', 'block'] as const
  if (task.status === 'BLOCKED') return ['unblock'] as const
  return [] as const
}
