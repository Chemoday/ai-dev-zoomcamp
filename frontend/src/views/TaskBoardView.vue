<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import TaskCard from '@/components/TaskCard.vue'
import { useAuthStore } from '@/stores/auth'
import { useHouseholdStore } from '@/stores/household'
import { STATUS_LABEL, type Task, type TaskStatus } from '@/types'
import { useTaskDisplay } from '@/composables/useTaskDisplay'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const store = useHouseholdStore()
const display = useTaskDisplay()

const hid = computed(() => Number(route.params.hid))
const str = (key: string) => (typeof route.query[key] === 'string' ? (route.query[key] as string) : '')

/**
 * Filters live in the URL, so a filtered board is linkable and "My tasks" in the
 * sidebar is just ?assignee=me. Narrowing is client-side until the API grows
 * query parameters.
 */
const view = computed(() => str('view') || 'kanban')
const zoneFilter = computed(() => str('zone'))
const statusFilter = computed(() => str('status'))
const assigneeFilter = computed(() => str('assignee'))

function setQuery(key: string, value: string) {
  const query = { ...route.query, [key]: value || undefined }
  router.replace({ name: 'tasks', params: { hid: hid.value }, query })
}

const filtered = computed(() => {
  let list = store.currentTasks
  if (zoneFilter.value) list = list.filter(t => String(t.zone) === zoneFilter.value)
  if (statusFilter.value) list = list.filter(t => t.status === statusFilter.value)
  if (assigneeFilter.value === 'me') list = list.filter(t => t.assignee === auth.myId)
  else if (assigneeFilter.value === 'none') list = list.filter(t => t.assignee === null)
  else if (assigneeFilter.value) list = list.filter(t => String(t.assignee) === assigneeFilter.value)
  return list
})

const columns = computed(() =>
  (['TODO', 'IN_PROGRESS', 'BLOCKED', 'DONE'] as TaskStatus[]).map(status => ({
    status,
    label: STATUS_LABEL[status],
    tasks: filtered.value.filter(t => t.status === status),
  })))

const activeFilters = computed(() =>
  [zoneFilter.value, statusFilter.value, assigneeFilter.value].filter(Boolean).length)

const flags = (task: Task) => {
  const list: string[] = []
  if (task.is_overdue) list.push('overdue')
  if (task.awaiting_approval) list.push('awaiting approval')
  return list.length ? '· ' + list.join(' · ') : ''
}
</script>

<template>
  <section class="page">
    <header class="head">
      <div>
        <h2>{{ assigneeFilter === 'me' ? 'My tasks' : 'Task board' }}</h2>
        <p class="text-muted lede">
          {{ assigneeFilter === 'me'
            ? 'Everything currently assigned to you in this household.'
            : 'All zones. Filters are in the URL, so a filtered board can be shared.' }}
        </p>
      </div>
      <RouterLink class="btn btn-primary" :to="{ name: 'task-create', params: { hid } }">+ New task</RouterLink>
    </header>

    <div class="filters">
      <div class="seg">
        <label class="seg-opt">
          <input type="radio" :checked="view === 'kanban'" @change="setQuery('view', 'kanban')">
          Kanban
        </label>
        <label class="seg-opt">
          <input type="radio" :checked="view === 'list'" @change="setQuery('view', 'list')">
          List
        </label>
      </div>
      <select class="input narrow" :value="zoneFilter" @change="setQuery('zone', ($event.target as HTMLSelectElement).value)">
        <option value="">All zones</option>
        <option v-for="zone in store.currentZones" :key="zone.id" :value="String(zone.id)">{{ zone.name }}</option>
      </select>
      <select class="input narrow" :value="assigneeFilter" @change="setQuery('assignee', ($event.target as HTMLSelectElement).value)">
        <option value="">Anyone</option>
        <option value="me">Assigned to me</option>
        <option value="none">Unassigned</option>
        <option v-for="member in store.currentMembers" :key="member.id" :value="String(member.user)">
          {{ store.userName(member.user) }}
        </option>
      </select>
      <select class="input narrow" :value="statusFilter" @change="setQuery('status', ($event.target as HTMLSelectElement).value)">
        <option value="">Any status</option>
        <option v-for="(label, status) in STATUS_LABEL" :key="status" :value="status">{{ label }}</option>
      </select>
      <span class="text-muted count">
        {{ activeFilters ? activeFilters + ' filter' + (activeFilters > 1 ? 's' : '') + ' · ' : '' }}
        {{ filtered.length }} of {{ store.currentTasks.length }}
      </span>
    </div>

    <div v-if="view === 'kanban'" class="board">
      <div v-for="column in columns" :key="column.status" class="column">
        <header class="column-head">
          <span class="column-label">{{ column.label }}</span>
          <span class="text-muted">{{ column.tasks.length }}</span>
        </header>
        <TaskCard v-for="task in column.tasks" :key="task.id" :task="task" :household-id="hid" />
      </div>
    </div>

    <div v-else class="table-wrap">
      <table class="table">
        <thead>
          <tr><th>Task</th><th>Zone</th><th>Assignee</th><th>Status</th><th>Due</th><th>Weight</th></tr>
        </thead>
        <tbody>
          <tr v-for="task in filtered" :key="task.id" @click="router.push({ name: 'task', params: { hid, tid: task.id } })">
            <td>{{ task.title }} <span class="flag">{{ flags(task) }}</span></td>
            <td class="text-muted">{{ display(task).zoneName }}</td>
            <td class="text-muted">{{ display(task).assigneeName }}</td>
            <td><span :class="display(task).statusClass">{{ display(task).statusLabel }}</span></td>
            <td class="text-muted">{{ display(task).deadlineLabel }}</td>
            <td class="text-muted">{{ task.weight }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-if="!filtered.length" class="text-muted empty">
      {{ store.currentTasks.length ? 'No tasks match these filters.' : 'No tasks in this household yet.' }}
    </p>
  </section>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--space-6); }
.head { display: flex; align-items: flex-end; justify-content: space-between; gap: var(--space-4); flex-wrap: wrap; }
h2 { margin: 0; }
.lede { margin: var(--space-2) 0 0; font-size: 14px; }
.filters { display: flex; align-items: center; gap: var(--space-4); flex-wrap: wrap; }
.narrow { width: auto; }
.count { font-size: 12px; }
.board { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: var(--space-4); align-items: start; }
.column { display: flex; flex-direction: column; gap: var(--space-3); min-width: 0; }
.column-head {
  display: flex; align-items: center; justify-content: space-between; gap: var(--space-2);
  padding-bottom: var(--space-2); font-size: 12px;
  background: linear-gradient(to right, var(--color-divider), transparent) no-repeat bottom / 100% 1px;
}
.column-label { font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; }
.table-wrap { overflow-x: auto; }
.table tbody tr { cursor: pointer; }
.flag { color: var(--color-accent-300); }
.empty { margin: 0; font-size: 14px; }
</style>
