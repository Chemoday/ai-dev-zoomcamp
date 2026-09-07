<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { useTaskDisplay } from '@/composables/useTaskDisplay'
import type { Task } from '@/types'

const props = defineProps<{ task: Task; householdId: number }>()
const display = useTaskDisplay()
const view = computed(() => display(props.task))
</script>

<template>
  <RouterLink class="card elev-sm task" :to="{ name: 'task', params: { hid: householdId, tid: task.id } }">
    <header class="task-head">
      <span class="card-title">{{ task.title }}</span>
      <span :class="view.statusClass">{{ view.statusLabel }}</span>
    </header>
    <div class="card-meta task-meta">
      <span>{{ view.zoneName }}</span>
      <span>{{ view.assigneeName }}</span>
      <span v-if="task.is_recurring">&#8635; every {{ task.interval_days }}d</span>
      <span>{{ view.deadlineLabel }}</span>
    </div>
    <p v-if="task.is_overdue" class="task-flag">Overdue</p>
    <p v-if="task.awaiting_approval" class="task-flag">Awaiting admin approval</p>
    <p v-if="task.blocked_reason" class="task-blocked">{{ task.blocked_reason }}</p>
    <p v-if="view.checklistLabel" class="card-meta">{{ view.checklistLabel }}</p>
  </RouterLink>
</template>

<style scoped>
.task { color: var(--color-text); text-decoration: none; gap: var(--space-2); }
.task:hover { box-shadow: var(--shadow-md); color: var(--color-text); }
.task-head { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-3); }
.card-title { text-wrap: pretty; }
.task-meta { gap: var(--space-4); flex-wrap: wrap; }
.task-flag { margin: 0; font-size: 12px; color: var(--color-accent-300); }
.task-blocked {
  margin: 0; padding: var(--space-2) var(--space-3); font-size: 12px;
  border-radius: var(--radius-sm); background: var(--color-neutral-900); color: var(--color-neutral-300);
}
</style>
