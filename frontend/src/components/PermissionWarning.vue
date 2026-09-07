<script setup lang="ts">
/**
 * Surfaces a place where the UI implies a restriction the backend does not
 * enforce. Membership creation and household/zone edits are open to any member
 * today; only task lifecycle and approve-by-admin are actually gated.
 */
defineProps<{ title?: string }>()
</script>

<template>
  <div class="card elev-sm warning">
    <div class="card-kicker">{{ title ?? 'Not enforced by the backend' }}</div>
    <p class="warning-body"><slot /></p>
  </div>
</template>

<style scoped>
.warning { background: var(--color-accent-900); gap: var(--space-2); }
.warning-body { margin: 0; font-size: 13px; color: var(--color-accent-100); }
</style>
