<script setup lang="ts">
import { computed, ref, watchEffect } from 'vue'
import { useRouter } from 'vue-router'
import PermissionWarning from '@/components/PermissionWarning.vue'
import { api } from '@/api'
import { useHouseholdStore } from '@/stores/household'
import { useUiStore } from '@/stores/ui'
import type { Mode } from '@/types'

const router = useRouter()
const store = useHouseholdStore()
const ui = useUiStore()

const name = ref('')
const mode = ref<Mode>('P2P')
watchEffect(() => {
  if (!store.current) return
  name.value = store.current.name
  mode.value = store.current.mode
})

const hid = computed(() => store.currentId ?? 0)

async function save() {
  await ui.run(async () => {
    await api.households.update(hid.value, { name: name.value, mode: mode.value })
    await store.load()
  }, 'Settings saved.')
}

async function remove() {
  const ok = await ui.run(async () => {
    await api.households.remove(hid.value)
    await store.load()
    return true
  }, 'Household deleted.')
  if (ok) {
    store.setCurrent(null)
    router.push({ name: 'households' })
  }
}
</script>

<template>
  <form class="page" @submit.prevent="save">
    <h2>Household settings</h2>

    <PermissionWarning>
      Renaming, switching governance mode and deleting zones are open to any member today. Treat the
      admin framing here as a convention, not a guarantee.
    </PermissionWarning>

    <div class="field">
      <label for="name">Name</label>
      <input id="name" v-model="name" class="input" required>
    </div>

    <div class="group">
      <p class="group-label">Governance mode</p>
      <div class="seg">
        <label class="seg-opt"><input v-model="mode" type="radio" value="P2P">Peer-to-peer</label>
        <label class="seg-opt"><input v-model="mode" type="radio" value="HIERARCHICAL">Hierarchical</label>
      </div>
      <p class="text-muted hint">
        Switching to peer-to-peer makes every "requires approval" flag inert; switching to hierarchical
        activates them again.
      </p>
    </div>

    <div class="actions">
      <button class="btn btn-primary" type="submit" :disabled="ui.busy">Save</button>
      <button class="btn btn-secondary" type="button" @click="remove">Delete household</button>
    </div>
  </form>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--space-6); max-width: 460px; }
h2 { margin: 0; }
.group { display: flex; flex-direction: column; gap: var(--space-2); }
.group-label { margin: 0; font-size: 12px; color: color-mix(in srgb, var(--color-text) 70%, transparent); }
.hint { margin: 0; font-size: 12px; }
.actions { display: flex; gap: var(--space-3); }
</style>
