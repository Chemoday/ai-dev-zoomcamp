<script setup lang="ts">
import { computed, ref, watchEffect } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import TaskCard from '@/components/TaskCard.vue'
import { api } from '@/api'
import { useHouseholdStore } from '@/stores/household'
import { useUiStore } from '@/stores/ui'

const route = useRoute()
const router = useRouter()
const store = useHouseholdStore()
const ui = useUiStore()

const hid = computed(() => Number(route.params.hid))
const zid = computed(() => Number(route.params.zid))
const zone = computed(() => store.zones.find(z => z.id === zid.value) ?? null)
const tasks = computed(() => store.currentTasks.filter(t => t.zone === zid.value))

const editing = ref(false)
const name = ref('')
const isShared = ref(true)
watchEffect(() => {
  if (!zone.value) return
  name.value = zone.value.name
  isShared.value = zone.value.is_shared
})

async function save() {
  const ok = await ui.run(async () => {
    await api.zones.update(zid.value, { name: name.value, is_shared: isShared.value })
    await store.load()
    return true
  }, 'Zone saved.')
  if (ok) editing.value = false
}

async function remove() {
  const ok = await ui.run(async () => {
    await api.zones.remove(zid.value)
    await store.load()
    return true
  }, 'Zone deleted.')
  if (ok) router.push({ name: 'zones', params: { hid: hid.value } })
}
</script>

<template>
  <section v-if="zone" class="page">
    <RouterLink class="btn btn-ghost back" :to="{ name: 'zones', params: { hid } }">&#8592; Zones</RouterLink>

    <header class="head">
      <div>
        <div class="titles">
          <h2>{{ zone.name }}</h2>
          <span :class="zone.is_shared ? 'tag tag-neutral' : 'tag tag-outline'">
            {{ zone.is_shared ? 'Shared' : 'Private' }}
          </span>
        </div>
        <p class="text-muted lede">
          {{ zone.is_shared ? 'Open to everyone in the household' : zone.residents.map(store.userName).join(', ') || 'No residents listed' }}
        </p>
      </div>
      <div class="actions">
        <RouterLink class="btn btn-primary" :to="{ name: 'task-create', params: { hid }, query: { zone: zone.id } }">
          + New task
        </RouterLink>
        <button class="btn btn-secondary" type="button" @click="editing = !editing">Edit zone</button>
        <button class="btn btn-secondary" type="button" @click="remove">Delete</button>
      </div>
    </header>

    <form v-if="editing" class="card elev-md form" @submit.prevent="save">
      <div class="field">
        <label for="zone-name">Zone name</label>
        <input id="zone-name" v-model="name" class="input" required>
      </div>
      <label class="radio">
        <input v-model="isShared" type="checkbox">
        <span class="dot square" />
        Shared space
      </label>
      <div class="actions">
        <button class="btn btn-primary" type="submit" :disabled="ui.busy">Save zone</button>
        <button class="btn btn-secondary" type="button" @click="editing = false">Cancel</button>
      </div>
    </form>

    <p v-if="!tasks.length" class="text-muted empty">No tasks in this zone yet.</p>
    <div class="grid">
      <TaskCard v-for="task in tasks" :key="task.id" :task="task" :household-id="hid" />
    </div>
  </section>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--space-6); max-width: 900px; }
.back { align-self: flex-start; }
.head { display: flex; align-items: flex-end; justify-content: space-between; gap: var(--space-4); flex-wrap: wrap; }
.titles { display: flex; align-items: center; gap: var(--space-3); flex-wrap: wrap; }
h2 { margin: 0; }
.lede { margin: var(--space-2) 0 0; font-size: 14px; }
.actions { display: flex; gap: var(--space-3); flex-wrap: wrap; }
.form { gap: var(--space-4); padding: var(--space-6); max-width: 440px; }
.square { border-radius: var(--radius-sm); }
.empty { margin: 0; font-size: 14px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: var(--space-4); }
</style>
