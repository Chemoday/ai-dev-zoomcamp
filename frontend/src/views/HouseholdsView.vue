<script setup lang="ts">
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useHouseholdStore } from '@/stores/household'
import { MODE_LABEL } from '@/types'

const router = useRouter()
const auth = useAuthStore()
const store = useHouseholdStore()

function open(id: number) {
  store.setCurrent(id)
  router.push({ name: 'dashboard', params: { hid: id } })
}

const roleIn = (householdId: number) => {
  const mine = store.memberships.find(m => m.household === householdId && m.user === auth.myId)
  if (!mine) return ''
  return mine.role === 'ADMIN' ? 'You are an admin' : 'You are a member'
}
const memberCount = (householdId: number) =>
  store.memberships.filter(m => m.household === householdId).length
</script>

<template>
  <section class="page">
    <header class="head">
      <div>
        <h2>My households</h2>
        <p class="text-muted lede">Roles are per household — you can be an admin in one and a member in another.</p>
      </div>
      <RouterLink class="btn btn-primary" :to="{ name: 'household-create' }">+ Create household</RouterLink>
    </header>

    <div v-if="!store.households.length" class="card elev-sm empty">
      <p class="card-kicker">Nothing here yet</p>
      <h3>You are not in a household</h3>
      <p class="card-body">
        Create one to get started. You will be its first admin automatically, and can add the people
        who already have accounts.
      </p>
      <RouterLink class="btn btn-primary" :to="{ name: 'household-create' }">Create household</RouterLink>
    </div>

    <div class="grid">
      <button
        v-for="household in store.households"
        :key="household.id"
        type="button"
        class="card elev-sm tile"
        @click="open(household.id)"
      >
        <div class="tile-head">
          <span class="card-title">{{ household.name }}</span>
          <span :class="household.mode === 'HIERARCHICAL' ? 'tag tag-accent' : 'tag tag-neutral'">
            {{ MODE_LABEL[household.mode] }}
          </span>
        </div>
        <div class="card-meta tile-meta">
          <span>{{ roleIn(household.id) }}</span>
          <span>{{ memberCount(household.id) }} members</span>
        </div>
      </button>
    </div>
  </section>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--space-6); max-width: 760px; }
.head { display: flex; align-items: flex-end; justify-content: space-between; gap: var(--space-4); flex-wrap: wrap; }
h2, h3 { margin: 0; }
.lede { margin: var(--space-2) 0 0; font-size: 14px; }
.empty { align-items: flex-start; gap: var(--space-4); padding: var(--space-8); }
.empty p { margin: 0; }
.card-body { max-width: 44ch; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: var(--space-4); }
.tile { cursor: pointer; text-align: left; border: 0; font: inherit; color: var(--color-text); }
.tile:hover { box-shadow: var(--shadow-md); }
.tile-head { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-3); }
.tile-meta { gap: var(--space-4); }
</style>
