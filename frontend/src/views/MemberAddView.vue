<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import PermissionWarning from '@/components/PermissionWarning.vue'
import { api } from '@/api'
import { useHouseholdStore } from '@/stores/household'
import { useUiStore } from '@/stores/ui'
import type { Role } from '@/types'

const route = useRoute()
const router = useRouter()
const store = useHouseholdStore()
const ui = useUiStore()

const hid = computed(() => Number(route.params.hid))
const username = ref('')
const role = ref<Role>('MEMBER')

/**
 * POST /api/memberships/ needs a user id, and there is no directory endpoint to
 * search: /api/users/ only returns people who already share a household. So the
 * lookup can only succeed for someone already visible, and otherwise the admin
 * has to supply the id out of band.
 */
async function submit() {
  const ok = await ui.run(async () => {
    const match = store.users.find(u => u.username === username.value.trim())
    if (!match) {
      throw new Error(
        'No user named "' + username.value.trim() + '" is visible to you. They need an account, ' +
        'created in the Django admin, and there is no directory to search.',
      )
    }
    await api.memberships.create({ user: match.id, household: hid.value, role: role.value })
    await store.load()
    return true
  }, 'Member added.')
  if (ok) router.push({ name: 'members', params: { hid: hid.value } })
}
</script>

<template>
  <form class="page" @submit.prevent="submit">
    <header>
      <h2>Add member</h2>
      <p class="text-muted lede">
        The person needs an existing account — there is no invite-by-email and no user directory to
        search. Ask whoever created the accounts for the exact username.
      </p>
    </header>

    <PermissionWarning>
      Any member can currently add people — and can create the new membership as an admin. This screen
      sits under settings for tidiness, not as a permission boundary.
    </PermissionWarning>

    <div class="field">
      <label for="username">Username</label>
      <input id="username" v-model="username" class="input" placeholder="rob" required>
    </div>

    <div class="roles">
      <p class="roles-label">Role</p>
      <div class="seg">
        <label class="seg-opt"><input v-model="role" type="radio" value="MEMBER">Member</label>
        <label class="seg-opt"><input v-model="role" type="radio" value="ADMIN">Admin</label>
      </div>
    </div>

    <div class="actions">
      <button class="btn btn-primary" type="submit" :disabled="ui.busy">Add to household</button>
      <RouterLink class="btn btn-secondary" :to="{ name: 'members', params: { hid } }">Cancel</RouterLink>
    </div>
  </form>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--space-6); max-width: 460px; }
h2 { margin: 0; }
.lede { margin: var(--space-2) 0 0; font-size: 14px; }
.roles { display: flex; flex-direction: column; gap: var(--space-2); }
.roles-label { margin: 0; font-size: 12px; color: color-mix(in srgb, var(--color-text) 70%, transparent); }
.actions { display: flex; gap: var(--space-3); }
</style>
