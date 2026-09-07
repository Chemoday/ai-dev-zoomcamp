<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { api } from '@/api'
import { useHouseholdStore } from '@/stores/household'
import { useUiStore } from '@/stores/ui'
import type { Mode } from '@/types'

const router = useRouter()
const store = useHouseholdStore()
const ui = useUiStore()

const name = ref('')
const mode = ref<Mode>('P2P')

async function submit() {
  const created = await ui.run(
    async () => {
      // The backend makes the creator an admin member atomically.
      const household = await api.households.create({ name: name.value, mode: mode.value })
      await store.load()
      return household
    },
    'Household created — you are its admin.',
  )
  if (created) {
    store.setCurrent(created.id)
    router.push({ name: 'dashboard', params: { hid: created.id } })
  }
}
</script>

<template>
  <form class="page" @submit.prevent="submit">
    <h2>Create household</h2>
    <div class="field">
      <label for="name">Name</label>
      <input id="name" v-model="name" class="input" placeholder="Flat 3B" required>
    </div>

    <fieldset class="modes">
      <legend>Governance mode</legend>
      <label class="radio option">
        <input v-model="mode" type="radio" value="P2P">
        <span class="dot" />
        <span>
          <strong>Peer-to-peer</strong><br>
          <span class="text-muted hint">
            Everyone equal. Completing a task always marks it done — approval flags are ignored.
          </span>
        </span>
      </label>
      <label class="radio option">
        <input v-model="mode" type="radio" value="HIERARCHICAL">
        <span class="dot" />
        <span>
          <strong>Hierarchical</strong><br>
          <span class="text-muted hint">
            Admins and members. Tasks marked "requires approval" wait for an admin before they count as done.
          </span>
        </span>
      </label>
    </fieldset>

    <div class="actions">
      <button class="btn btn-primary" type="submit" :disabled="ui.busy">Create</button>
      <RouterLink class="btn btn-secondary" :to="{ name: 'households' }">Cancel</RouterLink>
    </div>
  </form>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--space-6); max-width: 440px; }
h2 { margin: 0; }
.modes { display: flex; flex-direction: column; gap: var(--space-3); margin: 0; padding: 0; border: 0; }
legend { padding: 0 0 var(--space-3); font-size: 12px; color: color-mix(in srgb, var(--color-text) 70%, transparent); }
.option { align-items: flex-start; }
.option .dot { margin-top: 3px; }
.hint { font-size: 13px; }
.actions { display: flex; gap: var(--space-3); }
</style>
