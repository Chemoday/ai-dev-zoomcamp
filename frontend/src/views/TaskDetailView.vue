<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import SubtaskChecklist from '@/components/SubtaskChecklist.vue'
import { availableActions, useTaskDisplay } from '@/composables/useTaskDisplay'
import { useTaskActions, type LifecycleAction } from '@/composables/useTaskActions'
import { useHouseholdStore } from '@/stores/household'
import { useUiStore } from '@/stores/ui'

const route = useRoute()
const store = useHouseholdStore()
const ui = useUiStore()
const display = useTaskDisplay()
const { perform } = useTaskActions()

const hid = computed(() => Number(route.params.hid))
const tid = computed(() => Number(route.params.tid))
const task = computed(() => store.taskById(tid.value))
const view = computed(() => (task.value ? display(task.value) : null))

const LABELS: Record<LifecycleAction, string> = {
  start: 'Start', drop: 'Drop', block: 'Block', unblock: 'Unblock', complete: 'Complete', approve: 'Approve',
}
const PRIMARY: LifecycleAction[] = ['start', 'complete', 'unblock', 'approve']

const actions = computed(() => (task.value ? availableActions(task.value, store.isAdmin) : []))

const blockOpen = ref(false)
const reason = ref('')

async function run(action: LifecycleAction) {
  if (action === 'block') {
    blockOpen.value = true
    reason.value = ''
    return
  }
  await perform(action, tid.value)
}

async function submitBlock() {
  const done = await perform('block', tid.value, reason.value)
  if (done) blockOpen.value = false
}

const facts = computed(() => {
  const t = task.value
  if (!t || !view.value) return []
  return [
    { label: 'Zone', value: view.value.zoneName },
    { label: 'Assignee', value: view.value.assigneeName },
    { label: 'Deadline', value: view.value.deadlineLabel },
    { label: 'Weight', value: String(t.weight) },
    {
      label: 'Approval',
      value: t.requires_approval
        ? store.isHierarchical ? 'Admin approval required' : 'Flagged, ignored in peer-to-peer'
        : 'Not required',
    },
    { label: 'Repeats', value: t.is_recurring ? 'Every ' + t.interval_days + ' days' : 'One-off' },
  ]
})
</script>

<template>
  <section v-if="task && view" class="page">
    <RouterLink class="btn btn-ghost back" :to="{ name: 'tasks', params: { hid } }">&#8592; Task board</RouterLink>

    <header>
      <div class="titles">
        <span :class="view.statusClass">{{ view.statusLabel }}</span>
        <span v-if="task.is_overdue" class="tag tag-outline">Overdue</span>
        <span v-if="task.is_recurring" class="tag tag-neutral">&#8635; every {{ task.interval_days }} days</span>
      </div>
      <h2>{{ task.title }}</h2>
      <p v-if="task.description" class="description">{{ task.description }}</p>
    </header>

    <div v-if="task.awaiting_approval" class="card elev-sm approval">
      <p class="card-kicker">Awaiting admin approval</p>
      <p class="note">
        {{ store.isAdmin
          ? 'You can approve this — it moves straight to done.'
          : 'An admin needs to approve this before it counts as done.' }}
      </p>
    </div>

    <div v-if="task.blocked_reason" class="card elev-sm">
      <p class="card-kicker">Blocked</p>
      <p class="note reason">{{ task.blocked_reason }}</p>
    </div>

    <div v-if="task.status === 'DONE' && task.is_recurring" class="card elev-sm">
      <p class="card-kicker">Recurring</p>
      <p class="note">
        A new occurrence was created when this one was completed. It appears on the board as a fresh
        to-do — the API does not link the two.
      </p>
      <RouterLink class="btn btn-ghost self-start" :to="{ name: 'tasks', params: { hid } }">
        Open the task board
      </RouterLink>
    </div>

    <div class="actions">
      <button
        v-for="action in actions"
        :key="action"
        type="button"
        class="btn"
        :class="PRIMARY.includes(action) ? 'btn-primary' : 'btn-secondary'"
        :disabled="ui.busy"
        @click="run(action)"
      >
        {{ LABELS[action] }}
      </button>
      <RouterLink class="btn btn-secondary" :to="{ name: 'task-edit', params: { hid, tid } }">
        Edit details
      </RouterLink>
    </div>

    <form v-if="blockOpen" class="card elev-md block" @submit.prevent="submitBlock">
      <div class="field">
        <label for="reason">Why is it blocked?</label>
        <input id="reason" v-model="reason" class="input" placeholder="No descaler left" required>
      </div>
      <p class="text-muted hint">Free text — the API requires a reason but has no fixed list.</p>
      <div class="actions">
        <button class="btn btn-primary" type="submit" :disabled="ui.busy">Block task</button>
        <button class="btn btn-secondary" type="button" @click="blockOpen = false">Cancel</button>
      </div>
    </form>

    <dl class="facts">
      <div v-for="fact in facts" :key="fact.label">
        <dt>{{ fact.label }}</dt>
        <dd>{{ fact.value }}</dd>
      </div>
    </dl>

    <SubtaskChecklist :task-id="task.id" :subtasks="task.subtasks" />
  </section>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--space-6); max-width: 720px; }
.back, .self-start { align-self: flex-start; }
.titles { display: flex; align-items: center; gap: var(--space-3); flex-wrap: wrap; }
h2 { margin: var(--space-3) 0 0; text-wrap: pretty; }
.description { margin: var(--space-3) 0 0; font-size: 15px; opacity: 0.85; max-width: 60ch; }
.approval { background: var(--color-accent-900); }
.note { margin: 0; font-size: 14px; }
.reason { font-size: 15px; }
.actions { display: flex; gap: var(--space-3); flex-wrap: wrap; }
.block { gap: var(--space-3); padding: var(--space-6); max-width: 440px; }
.hint { margin: 0; font-size: 12px; }
.facts {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: var(--space-4);
  margin: 0; padding-top: var(--space-4);
  background: linear-gradient(to right, transparent, var(--color-divider) 48px,
    var(--color-divider) calc(100% - 48px), transparent) no-repeat top / 100% 1px;
}
dt { font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; color: color-mix(in srgb, var(--color-text) 55%, transparent); }
dd { margin: var(--space-1) 0 0; font-size: 15px; }
</style>
