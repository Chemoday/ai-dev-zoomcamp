<script setup lang="ts">
import { api } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useHouseholdStore } from '@/stores/household'
import { useUiStore } from '@/stores/ui'
import { MODE_LABEL, ROLE_LABEL } from '@/types'

const auth = useAuthStore()
const store = useHouseholdStore()
const ui = useUiStore()

/** Toggling your own away flag is always allowed, in every household. */
async function setAway(membershipId: number, is_away: boolean) {
  await ui.run(async () => {
    await api.memberships.update(membershipId, { is_away })
    await store.load()
  }, is_away ? 'Marked away.' : 'Back from away.')
}
</script>

<template>
  <section class="page">
    <header>
      <h2>{{ auth.me?.username }}</h2>
      <p class="text-muted lede">{{ auth.me?.email || 'No email on record' }}</p>
    </header>

    <section class="list">
      <h4>My households</h4>
      <div v-for="membership in store.myMemberships" :key="membership.id" class="card elev-sm row">
        <div class="row-main">
          <div class="row-titles">
            <span class="card-title">{{ store.households.find(h => h.id === membership.household)?.name }}</span>
            <span :class="membership.role === 'ADMIN' ? 'tag tag-accent' : 'tag tag-neutral'">
              {{ ROLE_LABEL[membership.role] }}
            </span>
            <span class="tag tag-neutral">
              {{ MODE_LABEL[store.households.find(h => h.id === membership.household)?.mode ?? 'P2P'] }}
            </span>
          </div>
          <label class="radio">
            <input
              type="checkbox"
              :checked="membership.is_away"
              @change="setAway(membership.id, ($event.target as HTMLInputElement).checked)"
            >
            <span class="dot square" />
            Away
          </label>
        </div>
      </div>
    </section>

    <p class="text-muted footnote">
      Signing out just discards the stored token — the API has no session to end, no password change
      and no account deletion.
    </p>
  </section>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--space-6); max-width: 640px; }
h2, h4 { margin: 0; }
.lede { margin: var(--space-2) 0 0; font-size: 14px; }
.list { display: flex; flex-direction: column; gap: var(--space-4); }
.row-main { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); flex-wrap: wrap; }
.row-titles { display: flex; align-items: center; gap: var(--space-3); flex-wrap: wrap; }
.square { border-radius: var(--radius-sm); }
.footnote { margin: 0; font-size: 13px; }
</style>
