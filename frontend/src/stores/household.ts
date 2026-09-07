import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api'
import { useAuthStore } from './auth'
import type { Household, Membership, Task, UserRef, Zone } from '@/types'

const CURRENT_KEY = 'chores.household'

/**
 * One cache for everything the caller can see. The API is household-scoped but
 * has no query parameters yet, so each list arrives whole and the getters below
 * narrow it to the current household. Once ?household= lands upstream, pass it
 * to the list() calls in load() and drop the client-side narrowing.
 */
export const useHouseholdStore = defineStore('household', () => {
  const auth = useAuthStore()

  const households = ref<Household[]>([])
  const memberships = ref<Membership[]>([])
  const zones = ref<Zone[]>([])
  const tasks = ref<Task[]>([])
  const users = ref<UserRef[]>([])
  const currentId = ref<number | null>(Number(localStorage.getItem(CURRENT_KEY)) || null)
  const loading = ref(false)
  const loaded = ref(false)

  async function load() {
    loading.value = true
    try {
      const [h, m, z, t, u] = await Promise.all([
        api.households.list(), api.memberships.list(), api.zones.list(), api.tasks.list(), api.users(),
      ])
      households.value = h; memberships.value = m; zones.value = z; tasks.value = t; users.value = u
      loaded.value = true
      if (currentId.value && !h.some(x => x.id === currentId.value)) setCurrent(null)
    } finally {
      loading.value = false
    }
  }

  async function ensureLoaded() { if (!loaded.value && auth.isAuthenticated) await load() }

  function setCurrent(id: number | null) {
    currentId.value = id
    if (id === null) localStorage.removeItem(CURRENT_KEY)
    else localStorage.setItem(CURRENT_KEY, String(id))
  }

  function reset() {
    households.value = []; memberships.value = []; zones.value = []; tasks.value = []; users.value = []
    loaded.value = false
    setCurrent(null)
  }

  const current = computed(() => households.value.find(h => h.id === currentId.value) ?? null)
  const myMembership = computed(() =>
    memberships.value.find(m => m.household === currentId.value && m.user === auth.myId) ?? null)
  const isAdmin = computed(() => myMembership.value?.role === 'ADMIN')
  const isHierarchical = computed(() => current.value?.mode === 'HIERARCHICAL')
  /** The approval queue only exists where both halves hold. */
  const canApprove = computed(() => isAdmin.value && isHierarchical.value)

  const currentZones = computed(() => zones.value.filter(z => z.household === currentId.value))
  const currentTasks = computed(() => {
    const ids = new Set(currentZones.value.map(z => z.id))
    return tasks.value.filter(t => ids.has(t.zone))
  })
  const currentMembers = computed(() => memberships.value.filter(m => m.household === currentId.value))
  const myMemberships = computed(() => memberships.value.filter(m => m.user === auth.myId))
  const awaitingApproval = computed(() => currentTasks.value.filter(t => t.awaiting_approval))
  const myOpenTasks = computed(() => currentTasks.value.filter(t => t.assignee === auth.myId && t.status !== 'DONE'))

  const userName = (id: number | null) =>
    id === null ? 'Unassigned' : users.value.find(u => u.id === id)?.username ?? 'Unknown user'
  const zoneName = (id: number) => zones.value.find(z => z.id === id)?.name ?? '—'
  const taskById = (id: number) => tasks.value.find(t => t.id === id) ?? null

  return {
    households, memberships, zones, tasks, users, currentId, loading, loaded,
    load, ensureLoaded, setCurrent, reset,
    current, myMembership, isAdmin, isHierarchical, canApprove,
    currentZones, currentTasks, currentMembers, myMemberships, awaitingApproval, myOpenTasks,
    userName, zoneName, taskById,
  }
})
