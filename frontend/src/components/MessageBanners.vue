<script setup lang="ts">
import { useUiStore } from '@/stores/ui'

const ui = useUiStore()
</script>

<template>
  <div v-if="ui.error || ui.notice" class="banners">
    <div v-if="ui.error" class="banner banner-error">
      <span>{{ ui.error }}</span>
      <button class="btn btn-ghost" type="button" @click="ui.clear()">Dismiss</button>
    </div>
    <p v-if="ui.notice" class="banner banner-notice">{{ ui.notice }}</p>
  </div>
</template>

<style scoped>
.banners { display: flex; flex-direction: column; gap: var(--space-3); }
.banner {
  display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-4);
  margin: 0; padding: var(--space-3) var(--space-4);
  font-size: 13px; border-radius: var(--radius-md); box-shadow: var(--shadow-sm);
}
.banner-error { background: var(--color-accent-900); color: var(--color-accent-200); }
.banner-notice { background: var(--color-neutral-900); color: var(--color-neutral-200); }
</style>
