import { ref } from 'vue'
import { defineStore } from 'pinia'
import { ApiError } from '@/api'

/**
 * One place for the banner pair every screen shows. The backend's own messages
 * ("A reason is required to block a task") are user-appropriate, so they are
 * surfaced verbatim rather than rewritten.
 */
export const useUiStore = defineStore('ui', () => {
  const error = ref<string | null>(null)
  const notice = ref<string | null>(null)
  const busy = ref(false)

  function clear() { error.value = null; notice.value = null }
  function fail(e: unknown) {
    error.value = e instanceof ApiError ? e.detail : e instanceof Error ? e.message : 'Something went wrong.'
    notice.value = null
  }

  /** Runs an API call, surfaces failures, and returns undefined when it failed. */
  async function run<T>(fn: () => Promise<T>, success?: string): Promise<T | undefined> {
    clear()
    busy.value = true
    try {
      const result = await fn()
      if (success) notice.value = success
      return result
    } catch (e) {
      fail(e)
      return undefined
    } finally {
      busy.value = false
    }
  }

  return { error, notice, busy, clear, fail, run }
})
