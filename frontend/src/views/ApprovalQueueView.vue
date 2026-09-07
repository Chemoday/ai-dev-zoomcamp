<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useTaskActions } from '@/composables/useTaskActions'
import { useHouseholdStore } from '@/stores/household'
import { useUiStore } from '@/stores/ui'

const route = useRoute()
const store = useHouseholdStore()
const ui = useUiStore()
const { perform } = useTaskActions()
const hid = computed(() => Number(route.params.hid))
</script>

<template>
  <section class="page">
    <header>
      <h2>Approval queue</h2>
      <p class="text-muted lede">
        Tasks their owner has marked complete, waiting on an admin. Only in hierarchical households.
      </p>
    </header>

    <p v-if="!store.awaitingApproval.length" class="text-muted empty">Nothing waiting on your approval.</p>

    <template v-else>
      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr><th>Task</th><th>Zone</th><th>Completed by</th><th /></tr>
          </thead>
          <tbody>
            <tr v-for="task in store.awaitingApproval" :key="task.id">
              <td>
                <RouterLink :to="{ name: 'task', params: { hid, tid: task.id } }">{{ task.title }}</RouterLink>
              </td>
              <td class="text-muted">{{ store.zoneName(task.zone) }}</td>
              <td class="text-muted">{{ store.userName(task.assignee) }}</td>
              <td class="right">
                <button class="btn btn-primary" type="button" :disabled="ui.busy" @click="perform('approve', task.id)">
                  Approve
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="text-muted footnote">
        The API records no timestamp for the completion event, so "when" is not shown.
      </p>
    </template>
  </section>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--space-6); max-width: 820px; }
h2 { margin: 0; }
.lede { margin: var(--space-2) 0 0; font-size: 14px; }
.empty { margin: 0; font-size: 14px; }
.table-wrap { overflow-x: auto; }
.right { text-align: right; }
.footnote { margin: 0; font-size: 12px; }
</style>
