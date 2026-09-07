<script setup lang="ts">
import { ref } from 'vue'
import { api } from '@/api'
import { useHouseholdStore } from '@/stores/household'
import { useUiStore } from '@/stores/ui'
import type { SubTask } from '@/types'

const props = defineProps<{ taskId: number; subtasks: SubTask[] }>()
const store = useHouseholdStore()
const ui = useUiStore()
const draft = ref('')

/** is_completed is directly writable by any member — one immediate PATCH, no gating. */
async function toggle(subtask: SubTask, checked: boolean) {
  await ui.run(async () => {
    await api.subtasks.update(subtask.id, { is_completed: checked })
    await store.load()
  })
}

async function add() {
  const title = draft.value.trim()
  if (!title) return
  await ui.run(async () => {
    await api.subtasks.create({ task: props.taskId, title })
    draft.value = ''
    await store.load()
  })
}
</script>

<template>
  <section class="checklist">
    <h4 class="checklist-head">Checklist</h4>
    <p v-if="!subtasks.length" class="text-muted empty">No checklist items.</p>
    <label v-for="subtask in subtasks" :key="subtask.id" class="radio item">
      <input
        type="checkbox"
        :checked="subtask.is_completed"
        @change="toggle(subtask, ($event.target as HTMLInputElement).checked)"
      >
      <span class="dot square" />
      <span :class="{ complete: subtask.is_completed }">{{ subtask.title }}</span>
    </label>
    <form class="add" @submit.prevent="add">
      <input v-model="draft" class="input" placeholder="Add a checklist item">
      <button class="btn btn-secondary" type="submit">Add</button>
    </form>
  </section>
</template>

<style scoped>
.checklist { display: flex; flex-direction: column; gap: var(--space-3); }
.checklist-head { margin: 0; }
.empty, .item { margin: 0; font-size: 14px; }
.item { gap: var(--space-3); }
.square { border-radius: var(--radius-sm); }
.complete { opacity: 0.5; }
.add { display: flex; gap: var(--space-3); max-width: 420px; margin-top: var(--space-2); }
</style>
