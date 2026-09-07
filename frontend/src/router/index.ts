import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useHouseholdStore } from '@/stores/household'
import { useUiStore } from '@/stores/ui'

// meta.chrome: false → no header/sidebar (login only)
// meta.household: true → the route carries :hid and selects that household
const routes: RouteRecordRaw[] = [
  { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue'), meta: { chrome: false, public: true } },
  { path: '/', redirect: { name: 'households' } },
  { path: '/households', name: 'households', component: () => import('@/views/HouseholdsView.vue') },
  { path: '/households/new', name: 'household-create', component: () => import('@/views/HouseholdCreateView.vue') },
  { path: '/profile', name: 'profile', component: () => import('@/views/ProfileView.vue') },
  {
    path: '/h/:hid(\\d+)',
    meta: { household: true },
    children: [
      { path: '', redirect: { name: 'dashboard' } },
      { path: 'dashboard', name: 'dashboard', component: () => import('@/views/DashboardView.vue') },
      { path: 'zones', name: 'zones', component: () => import('@/views/ZonesView.vue') },
      { path: 'zones/:zid(\\d+)', name: 'zone', component: () => import('@/views/ZoneDetailView.vue') },
      { path: 'tasks', name: 'tasks', component: () => import('@/views/TaskBoardView.vue') },
      { path: 'tasks/new', name: 'task-create', component: () => import('@/views/TaskFormView.vue') },
      { path: 'tasks/:tid(\\d+)', name: 'task', component: () => import('@/views/TaskDetailView.vue') },
      { path: 'tasks/:tid(\\d+)/edit', name: 'task-edit', component: () => import('@/views/TaskFormView.vue') },
      { path: 'approvals', name: 'approvals', component: () => import('@/views/ApprovalQueueView.vue'), meta: { requiresApproval: true } },
      { path: 'members', name: 'members', component: () => import('@/views/MembersView.vue') },
      { path: 'members/add', name: 'member-add', component: () => import('@/views/MemberAddView.vue') },
      { path: 'members/:mid(\\d+)', name: 'member', component: () => import('@/views/MemberDetailView.vue') },
      { path: 'settings', name: 'settings', component: () => import('@/views/HouseholdSettingsView.vue') },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: { name: 'households' } },
]

export const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach(async to => {
  const auth = useAuthStore()
  const store = useHouseholdStore()
  useUiStore().clear()

  if (!auth.isAuthenticated) return to.meta.public ? true : { name: 'login', query: { next: to.fullPath } }
  await auth.restore()
  if (!auth.isAuthenticated) return { name: 'login' }
  if (to.meta.public) return { name: 'households' }

  await store.ensureLoaded()

  if (to.meta.household) {
    const hid = Number(to.params.hid)
    if (!store.households.some(h => h.id === hid)) return { name: 'households' }
    store.setCurrent(hid)
  }

  // The approval queue is meaningless outside "admin of a hierarchical household".
  if (to.meta.requiresApproval && !store.canApprove) return { name: 'dashboard', params: to.params }
  return true
})
