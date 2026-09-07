<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useHouseholdStore } from '@/stores/household'
import { useUiStore } from '@/stores/ui'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const store = useHouseholdStore()
const ui = useUiStore()

const username = ref('')
const password = ref('')

async function submit() {
  const ok = await ui.run(async () => {
    await auth.login(username.value, password.value)
    await store.load()
    return true
  })
  if (!ok) return
  const next = typeof route.query.next === 'string' ? route.query.next : null
  if (next) return router.push(next)
  if (store.households.length === 1) {
    const only = store.households[0]
    store.setCurrent(only.id)
    return router.push({ name: 'dashboard', params: { hid: only.id } })
  }
  router.push({ name: 'households' })
}
</script>

<template>
  <div class="page">
    <div class="panel">
      <div>
        <p class="kicker">Shared household chores</p>
        <h1>Sign in</h1>
        <p class="text-muted intro">
          Accounts are created by your household admin. There is no self-registration and no password
          reset — if you are locked out, contact your admin.
        </p>
      </div>

      <form class="form" @submit.prevent="submit">
        <div class="field">
          <label for="username">Username</label>
          <input id="username" v-model="username" class="input" autocomplete="username">
        </div>
        <div class="field">
          <label for="password">Password</label>
          <input id="password" v-model="password" class="input" type="password" autocomplete="current-password">
        </div>
        <p v-if="ui.error" class="error">{{ ui.error }}</p>
        <button class="btn btn-primary btn-block" type="submit" :disabled="ui.busy">
          {{ ui.busy ? 'Signing in…' : 'Sign in' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh; display: grid; align-content: center; justify-items: start;
  padding: clamp(24px, 7vw, 96px);
  background: radial-gradient(120% 90% at 8% 0%, #1d2036 0%, var(--color-bg) 62%);
}
.panel { width: 100%; max-width: 380px; display: flex; flex-direction: column; gap: var(--space-6); }
.kicker {
  margin: 0 0 var(--space-3); font-size: 11px; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--color-accent);
}
h1 { margin: 0; font-size: clamp(34px, 5vw, 46px); }
.intro { margin: var(--space-3) 0 0; font-size: 14px; }
.form { display: flex; flex-direction: column; gap: var(--space-4); }
.error {
  margin: 0; padding: var(--space-3); font-size: 13px; border-radius: var(--radius-md);
  background: var(--color-neutral-900); box-shadow: var(--shadow-sm); color: var(--color-accent-200);
}
</style>
