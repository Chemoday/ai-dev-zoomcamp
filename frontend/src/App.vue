<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter, type RouteLocationRaw } from 'vue-router'
import MessageBanners from '@/components/MessageBanners.vue'
import { useAuthStore } from '@/stores/auth'
import { useHouseholdStore } from '@/stores/household'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const store = useHouseholdStore()

const chrome = computed(() => route.meta.chrome !== false)
const showSidebar = computed(() => Boolean(store.current) && route.meta.household === true)
const hid = computed(() => store.currentId ?? 0)

const navItems = computed(() => {
  const items: { label: string; to: RouteLocationRaw; count: number }[] = [
    { label: 'Dashboard', to: { name: 'dashboard', params: { hid: hid.value } }, count: 0 },
    { label: 'Zones', to: { name: 'zones', params: { hid: hid.value } }, count: store.currentZones.length },
    { label: 'Task board', to: { name: 'tasks', params: { hid: hid.value } }, count: 0 },
    { label: 'My tasks', to: { name: 'tasks', params: { hid: hid.value }, query: { assignee: 'me' } }, count: store.myOpenTasks.length },
  ]
  if (store.canApprove) {
    items.push({ label: 'Approvals', to: { name: 'approvals', params: { hid: hid.value } }, count: store.awaitingApproval.length })
  }
  items.push(
    { label: 'Members', to: { name: 'members', params: { hid: hid.value } }, count: store.currentMembers.length },
    { label: 'Settings', to: { name: 'settings', params: { hid: hid.value } }, count: 0 },
    { label: 'Profile', to: { name: 'profile' }, count: 0 },
  )
  return items
})

function switchHousehold(event: Event) {
  const id = Number((event.target as HTMLSelectElement).value)
  store.setCurrent(id)
  router.push({ name: 'dashboard', params: { hid: id } })
}

function signOut() {
  auth.logout()
  store.reset()
  router.push({ name: 'login' })
}
</script>

<template>
  <RouterView v-if="!chrome" />
  <div v-else class="shell">
    <header class="nav shell-head">
      <div class="nav-brand brand">
        <RouterLink :to="{ name: 'households' }" class="brand-mark">Chores</RouterLink>
        <span v-if="store.current" class="brand-household">{{ store.current.name }}</span>
      </div>
      <select
        v-if="store.households.length > 1 && store.currentId"
        class="input switcher"
        :value="String(store.currentId)"
        @change="switchHousehold"
      >
        <option v-for="household in store.households" :key="household.id" :value="String(household.id)">
          {{ household.name }}
        </option>
      </select>
      <div class="head-right">
        <RouterLink :to="{ name: 'profile' }">{{ auth.me?.username ?? 'me' }}</RouterLink>
        <button class="btn btn-secondary" type="button" @click="signOut">Sign out</button>
      </div>
    </header>

    <div class="shell-body">
      <nav v-if="showSidebar" class="nav side">
        <RouterLink v-for="item in navItems" :key="item.label" :to="item.to" class="side-link">
          <span>{{ item.label }}</span>
          <span v-if="item.count" class="side-count">{{ item.count }}</span>
        </RouterLink>
      </nav>
      <main class="shell-main">
        <MessageBanners />
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.shell { min-height: 100vh; display: flex; flex-direction: column; }
.shell-head {
  gap: var(--space-6); padding: var(--space-4) clamp(16px, 3vw, 32px);
  background: linear-gradient(to right, transparent, var(--color-divider) 48px,
    var(--color-divider) calc(100% - 48px), transparent) no-repeat bottom / 100% 1px;
}
.brand { display: flex; align-items: baseline; gap: var(--space-3); margin-right: auto; min-width: 0; }
.brand-mark { color: var(--color-text); text-decoration: none; }
.brand-household {
  font-size: 13px; font-weight: 400; max-width: 26ch; white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis;
  color: color-mix(in srgb, var(--color-text) 60%, transparent);
}
.switcher { width: auto; max-width: 200px; }
.head-right { display: flex; align-items: center; gap: var(--space-4); font-size: 14px; }
.shell-body { display: flex; align-items: flex-start; flex: 1; flex-wrap: wrap; }
.side {
  flex-direction: column; align-items: stretch; gap: var(--space-1);
  width: 200px; flex: none; padding: var(--space-6) var(--space-4);
}
.side-link {
  display: flex; justify-content: space-between; gap: var(--space-2);
  padding: var(--space-2) var(--space-3); border-radius: var(--radius-sm);
  color: inherit; text-decoration: none; white-space: nowrap;
}
.side-link:hover { background: color-mix(in srgb, var(--color-text) 6%, transparent); }
.side-link.router-link-exact-active { color: var(--color-accent); }
.side-count { font-size: 12px; color: var(--color-accent-300); }
.shell-main {
  flex: 1 1 420px; min-width: 0; display: flex; flex-direction: column; gap: var(--space-6);
  padding: var(--space-8) clamp(16px, 3vw, 32px) 96px;
}
</style>
