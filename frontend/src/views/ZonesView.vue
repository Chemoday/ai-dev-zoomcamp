<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'
import PermissionWarning from '@/components/PermissionWarning.vue'
import { api } from '@/api'
import { useHouseholdStore } from '@/stores/household'
import { useUiStore } from '@/stores/ui'

const store = useHouseholdStore()
const ui = useUiStore()
const hid = computed(() => store.currentId ?? 0)

const formOpen = ref(false)
const name = ref('')
const isShared = ref(true)
const residents = ref<number[]>([])

const openCount = (zoneId: number) =>
  store.currentTasks.filter(t => t.zone === zoneId && t.status !== 'DONE').length

function toggleForm() {
  formOpen.value = !formOpen.value
  name.value = ''
  isShared.value = true
  residents.value = []
}

async function submit() {
  const ok = await ui.run(async () => {
    await api.zones.create({
      household: hid.value,
      name: name.value,
      is_shared: isShared.value,
      residents: isShared.value ? [] : residents.value,
    })
    await store.load()
    return true
  }, 'Zone added.')
  if (ok) formOpen.value = false
}
</script>

<template>
  <section class="page">
    <header class="head">
      <h2>Zones</h2>
      <button class="btn btn-primary" type="button" @click="toggleForm">
        {{ formOpen ? 'Close' : '+ Add zone' }}
      </button>
    </header>

    <PermissionWarning>
      Zones can be created, edited and deleted by any member of this household — the backend does not
      restrict it to admins.
    </PermissionWarning>

    <form v-if="formOpen" class="card elev-md form" @submit.prevent="submit">
      <div class="field">
        <label for="zone-name">Zone name</label>
        <input id="zone-name" v-model="name" class="input" placeholder="Bathroom" required>
      </div>
      <label class="radio">
        <input v-model="isShared" type="checkbox">
        <span class="dot square" />
        Shared space
      </label>
      <div v-if="!isShared" class="residents">
        <p class="residents-label">Residents</p>
        <div class="residents-list">
          <label v-for="member in store.currentMembers" :key="member.id" class="radio">
            <input v-model="residents" type="checkbox" :value="member.user">
            <span class="dot square" />
            {{ store.userName(member.user) }}
          </label>
        </div>
      </div>
      <div class="actions">
        <button class="btn btn-primary" type="submit" :disabled="ui.busy">Add zone</button>
        <button class="btn btn-secondary" type="button" @click="toggleForm">Cancel</button>
      </div>
    </form>

    <p v-if="!store.currentZones.length" class="text-muted empty">
      No zones yet. Add a room or shared space to hang tasks off.
    </p>
    <div class="grid">
      <RouterLink
        v-for="zone in store.currentZones"
        :key="zone.id"
        class="card elev-sm tile"
        :to="{ name: 'zone', params: { hid, zid: zone.id } }"
      >
        <div class="tile-head">
          <span class="card-title">{{ zone.name }}</span>
          <span :class="zone.is_shared ? 'tag tag-neutral' : 'tag tag-outline'">
            {{ zone.is_shared ? 'Shared' : 'Private' }}
          </span>
        </div>
        <div class="card-meta tile-meta">
          <span>{{ openCount(zone.id) }} open</span>
          <span>{{ zone.is_shared ? 'Everyone' : zone.residents.map(store.userName).join(', ') || 'No residents listed' }}</span>
        </div>
      </RouterLink>
    </div>
  </section>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--space-6); max-width: 900px; }
.head { display: flex; align-items: flex-end; justify-content: space-between; gap: var(--space-4); flex-wrap: wrap; }
h2 { margin: 0; }
.form { gap: var(--space-4); padding: var(--space-6); max-width: 440px; }
.square { border-radius: var(--radius-sm); }
.residents { display: flex; flex-direction: column; gap: var(--space-2); }
.residents-label { margin: 0; font-size: 12px; color: color-mix(in srgb, var(--color-text) 70%, transparent); }
.residents-list { display: flex; flex-wrap: wrap; gap: var(--space-3); }
.actions { display: flex; gap: var(--space-3); }
.empty { margin: 0; font-size: 14px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: var(--space-4); }
.tile { color: var(--color-text); text-decoration: none; }
.tile:hover { box-shadow: var(--shadow-md); color: var(--color-text); }
.tile-head { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-3); }
.tile-meta { gap: var(--space-4); flex-wrap: wrap; }
</style>
