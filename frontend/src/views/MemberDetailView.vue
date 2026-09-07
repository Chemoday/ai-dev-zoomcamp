<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { api } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useHouseholdStore } from '@/stores/household'
import { useUiStore } from '@/stores/ui'
import { ROLE_LABEL, type Role } from '@/types'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const store = useHouseholdStore()
const ui = useUiStore()

const hid = computed(() => Number(route.params.hid))
const mid = computed(() => Number(route.params.mid))
const membership = computed(() => store.memberships.find(m => m.id === mid.value) ?? null)
const isMe = computed(() => membership.value?.user === auth.myId)

/** Role changes are admin-gated in the serializer; away is self-or-admin. */
async function setRole(role: Role) {
  await ui.run(async () => {
    await api.memberships.update(mid.value, { role })
    await store.load()
  }, 'Role updated.')
}

async function setAway(is_away: boolean) {
  await ui.run(async () => {
    await api.memberships.update(mid.value, { is_away })
    await store.load()
  }, is_away ? 'Marked away — excluded from new assignments.' : 'Back from away.')
}

async function remove() {
  const ok = await ui.run(async () => {
    await api.memberships.remove(mid.value)
    await store.load()
    return true
  }, 'Removed from household.')
  if (ok) router.push({ name: 'members', params: { hid: hid.value } })
}
</script>

<template>
  <section v-if="membership" class="page">
    <RouterLink class="btn btn-ghost back" :to="{ name: 'members', params: { hid } }">&#8592; Members</RouterLink>

    <header>
      <h2>{{ store.userName(membership.user) }}</h2>
      <p class="text-muted lede">
        {{ ROLE_LABEL[membership.role] }} of {{ store.current?.name }}<span v-if="isMe"> — this is you</span>
      </p>
    </header>

    <div class="group">
      <p class="group-label">Role in {{ store.current?.name }}</p>
      <div class="seg">
        <label class="seg-opt">
          <input type="radio" :checked="membership.role === 'MEMBER'" @change="setRole('MEMBER')">Member
        </label>
        <label class="seg-opt">
          <input type="radio" :checked="membership.role === 'ADMIN'" @change="setRole('ADMIN')">Admin
        </label>
      </div>
      <p v-if="!store.isAdmin" class="text-muted hint">
        Only an admin can change a role — the API will reject this.
      </p>
    </div>

    <label class="radio">
      <input type="checkbox" :checked="membership.is_away" @change="setAway(($event.target as HTMLInputElement).checked)">
      <span class="dot square" />
      Away — excluded from new assignments
    </label>
    <p v-if="!isMe && !store.isAdmin" class="text-muted hint">
      You can only change your own away status.
    </p>

    <button class="btn btn-secondary self-start" type="button" @click="remove">Remove from household</button>
  </section>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--space-6); max-width: 520px; }
.back, .self-start { align-self: flex-start; }
h2 { margin: 0; }
.lede { margin: var(--space-2) 0 0; font-size: 14px; }
.group { display: flex; flex-direction: column; gap: var(--space-3); }
.group-label { margin: 0; font-size: 12px; color: color-mix(in srgb, var(--color-text) 70%, transparent); }
.hint { margin: 0; font-size: 12px; }
.square { border-radius: var(--radius-sm); }
</style>
