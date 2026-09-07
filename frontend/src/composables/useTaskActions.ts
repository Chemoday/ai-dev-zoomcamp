import { api } from '@/api'
import { useHouseholdStore } from '@/stores/household'
import { useUiStore } from '@/stores/ui'
import type { Task } from '@/types'

export type LifecycleAction = 'start' | 'drop' | 'block' | 'unblock' | 'complete' | 'approve'

/**
 * The six POST actions, each followed by a reload — completing a recurring task
 * spawns a sibling the response body does not mention, so the list has to be
 * re-fetched to see it.
 */
export function useTaskActions() {
  const store = useHouseholdStore()
  const ui = useUiStore()

  function outcome(action: LifecycleAction, task: Task): string {
    if (action === 'approve') return 'Approved — marked done.'
    if (action === 'start') return 'Started, and assigned to you.'
    if (action === 'drop') return 'Dropped back to the unassigned pool.'
    if (action === 'unblock') return 'Unblocked.'
    if (task.awaiting_approval) return 'Marked complete — waiting on an admin to approve it.'
    if (task.status === 'DONE' && task.is_recurring) return 'Done. The next occurrence is on the board.'
    return 'Done.'
  }

  async function perform(action: LifecycleAction, id: number, reason?: string) {
    return ui.run(async () => {
      const task = action === 'block'
        ? await api.tasks.block(id, reason ?? '')
        : await api.tasks[action](id)
      await store.load()
      ui.notice = action === 'block' ? 'Task blocked.' : outcome(action, task)
      return task
    })
  }

  return { perform }
}
