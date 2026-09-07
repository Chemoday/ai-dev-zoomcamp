<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import TaskCard from '@/components/TaskCard.vue'
import { useHouseholdStore } from '@/stores/household'
import { MODE_LABEL } from '@/types'

const store = useHouseholdStore()
const hid = computed(() => store.currentId ?? 0)

const tiles = computed(() => {
  const list = [
    { label: 'Open tasks', value: store.currentTasks.filter(t => t.status !== 'DONE').length, hint: 'Not done yet', to: { name: 'tasks', params: { hid: hid.value } }, accent: false },
    { label: 'Overdue', value: store.currentTasks.filter(t => t.is_overdue).length, hint: 'Past deadline', to: { name: 'tasks', params: { hid: hid.value } }, accent: true },
    { label: 'Blocked', value: store.currentTasks.filter(t => t.status === 'BLOCKED').length, hint: 'Waiting on something', to: { name: 'tasks', params: { hid: hid.value }, query: { status: 'BLOCKED' } }, accent: true },
  ]
  if (store.canApprove) {
    list.push({ label: 'Awaiting approval', value: store.awaitingApproval.length, hint: 'Your call', to: { name: 'approvals', params: { hid: hid.value } }, accent: true })
  }
  return list
})

const attention = computed(() =>
  store.currentTasks.filter(t => t.is_overdue || t.status === 'BLOCKED' || t.awaiting_approval).slice(0, 6))
</script>

<template>
  <section v-if="store.current" class="page">
    <header>
      <div class="titles">
        <h2>{{ store.current.name }}</h2>
        <span :class="store.isHierarchical ? 'tag tag-accent' : 'tag tag-neutral'">
          {{ MODE_LABEL[store.current.mode] }}
        </span>
        <span class="tag tag-neutral">You: {{ store.isAdmin ? 'Admin' : 'Member' }}</span>
        <span v-if="store.myMembership?.is_away" class="tag tag-outline">Away</span>
      </div>
      <p class="text-muted lede">
        {{ store.isHierarchical
          ? 'Admins approve tasks flagged as needing it. Everyone else can start, block and complete.'
          : 'Everyone has equal permissions here — completing a task marks it done straight away.' }}
      </p>
    </header>

    <div v-if="!store.currentZones.length" class="card elev-sm empty">
      <p class="card-kicker">First step</p>
      <h3>Add your first zone</h3>
      <p class="card-body">
        Tasks live inside zones — a room or a shared space. Create one, then the task board has
        somewhere to put chores.
      </p>
      <RouterLink class="btn btn-primary" :to="{ name: 'zones', params: { hid } }">Go to zones</RouterLink>
    </div>

    <div class="tiles">
      <RouterLink v-for="tile in tiles" :key="tile.label" class="card elev-sm tile" :to="tile.to">
        <span class="tile-value" :class="{ accent: tile.accent && tile.value > 0 }">{{ tile.value }}</span>
        <span class="tile-label">{{ tile.label }}</span>
        <span class="card-meta">{{ tile.hint }}</span>
      </RouterLink>
    </div>

    <section class="attention">
      <h4>Needs attention</h4>
      <p v-if="!attention.length" class="text-muted empty-line">Nothing overdue, blocked or waiting.</p>
      <div v-else class="grid">
        <TaskCard v-for="task in attention" :key="task.id" :task="task" :household-id="hid" />
      </div>
    </section>
  </section>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--space-8); max-width: 900px; }
.titles { display: flex; align-items: center; gap: var(--space-3); flex-wrap: wrap; }
h2, h3, h4 { margin: 0; }
.lede { margin: var(--space-3) 0 0; font-size: 14px; }
.empty { align-items: flex-start; gap: var(--space-4); padding: var(--space-8); }
.empty p { margin: 0; }
.card-body { max-width: 46ch; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: var(--space-4); }
.tile { gap: var(--space-1); color: var(--color-text); text-decoration: none; }
.tile:hover { box-shadow: var(--shadow-md); color: var(--color-text); }
.tile-value { font-family: var(--font-heading); font-size: 38px; line-height: 1.1; }
.tile-value.accent { color: var(--color-accent-300); }
.tile-label { font-size: 13px; }
.attention { display: flex; flex-direction: column; gap: var(--space-4); }
.empty-line { margin: 0; font-size: 14px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: var(--space-4); }
</style>
