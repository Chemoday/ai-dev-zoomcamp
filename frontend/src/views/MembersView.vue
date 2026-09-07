<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useHouseholdStore } from '@/stores/household'
import { ROLE_LABEL } from '@/types'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const store = useHouseholdStore()
const hid = computed(() => Number(route.params.hid))
</script>

<template>
  <section class="page">
    <header class="head">
      <h2>Members</h2>
      <RouterLink class="btn btn-primary" :to="{ name: 'member-add', params: { hid } }">+ Add member</RouterLink>
    </header>

    <table class="table">
      <thead>
        <tr><th>Person</th><th>Role</th><th>Status</th></tr>
      </thead>
      <tbody>
        <tr
          v-for="member in store.currentMembers"
          :key="member.id"
          @click="router.push({ name: 'member', params: { hid, mid: member.id } })"
        >
          <td>
            {{ store.userName(member.user) }}
            <span v-if="member.user === auth.myId" class="text-muted">(you)</span>
          </td>
          <td><span :class="member.role === 'ADMIN' ? 'tag tag-accent' : 'tag tag-neutral'">{{ ROLE_LABEL[member.role] }}</span></td>
          <td class="text-muted">{{ member.is_away ? 'Away' : 'Available' }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--space-6); max-width: 760px; }
.head { display: flex; align-items: flex-end; justify-content: space-between; gap: var(--space-4); flex-wrap: wrap; }
h2 { margin: 0; }
.table tbody tr { cursor: pointer; }
</style>
