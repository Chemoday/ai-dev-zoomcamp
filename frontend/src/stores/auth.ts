import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api'
import type { Me } from '@/types'

const TOKEN_KEY = 'chores.token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const me = ref<Me | null>(null)
  const isAuthenticated = computed(() => token.value !== null)
  const myId = computed(() => me.value?.id ?? null)

  async function login(username: string, password: string) {
    const { token: fresh } = await api.login(username, password)
    token.value = fresh
    localStorage.setItem(TOKEN_KEY, fresh)
    me.value = await api.me()
  }

  /** Re-hydrate identity from a stored token on a hard refresh. */
  async function restore() {
    if (!token.value || me.value) return
    try { me.value = await api.me() } catch { logout() }
  }

  /** The API has no token revocation — signing out is discarding the token. */
  function logout() {
    token.value = null
    me.value = null
    localStorage.removeItem(TOKEN_KEY)
  }

  return { token, me, myId, isAuthenticated, login, restore, logout }
})
