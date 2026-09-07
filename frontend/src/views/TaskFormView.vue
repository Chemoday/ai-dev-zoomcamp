<script setup lang="ts">
import { computed, ref, watchEffect } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/api'
import { useHouseholdStore } from '@/stores/household'
import { useUiStore } from '@/stores/ui'
import type { TaskInput } from '@/types'

const route = useRoute()
const router = useRouter()
const store = useHouseholdStore()
const ui = useUiStore()

const hid = computed(() => Number(route.params.hid))
const tid = computed(() => (route.params.tid ? Number(route.params.tid) : null))
const editing = computed(() => tid.value !== null)

const zone = ref<number | null>(null)
const title = ref('')
const description = ref('')
const requiresApproval = ref(false)
const isRecurring = ref(false)
const intervalDays = ref(7)
const deadline = ref('')
const weight = ref(1)

/** datetime-local wants "YYYY-MM-DDTHH:mm" in local time; the API wants ISO. */
const toLocalInput = (iso: string | null) => {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + 'T' + pad(d.getHours()) + ':' + pad(d.getMinutes())
}

watchEffect(() => {
  const existing = tid.value ? store.taskById(tid.value) : null
  if (existing) {
    zone.value = existing.zone
    title.value = existing.title
    description.value = existing.description
    requiresApproval.value = existing.requires_approval
    isRecurring.value = existing.is_recurring
    intervalDays.value = existing.interval_days ?? 7
    deadline.value = toLocalInput(existing.deadline)
    weight.value = existing.weight
    return
  }
  if (zone.value === null) {
    const preset = typeof route.query.zone === 'string' ? Number(route.query.zone) : null
    zone.value = preset ?? store.currentZones[0]?.id ?? null
  }
})

async function submit() {
  if (zone.value === null) return
  const payload: TaskInput = {
    zone: zone.value,
    title: title.value,
    description: description.value,
    requires_approval: requiresApproval.value,
    is_recurring: isRecurring.value,
    interval_days: isRecurring.value ? Number(intervalDays.value) || 1 : null,
    deadline: deadline.value ? new Date(deadline.value).toISOString() : null,
    weight: Number(weight.value) || 1,
  }
  const saved = await ui.run(async () => {
    // status / assignee / blocked_reason / awaiting_approval are read-only here
    // by construction: TaskInput cannot carry them.
    const task = editing.value && tid.value
      ? await api.tasks.update(tid.value, payload)
      : await api.tasks.create(payload)
    await store.load()
    return task
  }, 'Task saved.')
  if (saved) router.push({ name: 'task', params: { hid: hid.value, tid: saved.id } })
}

function cancel() {
  if (editing.value && tid.value) router.push({ name: 'task', params: { hid: hid.value, tid: tid.value } })
  else router.push({ name: 'tasks', params: { hid: hid.value } })
}
</script>

<template>
  <form class="page" @submit.prevent="submit">
    <header>
      <h2>{{ editing ? 'Edit task' : 'New task' }}</h2>
      <p class="text-muted lede">
        Status, assignee and blocked reason are driven by the lifecycle actions on the task itself,
        not by this form.
      </p>
    </header>

    <div class="field">
      <label for="zone">Zone</label>
      <select id="zone" v-model="zone" class="input" required>
        <option v-for="option in store.currentZones" :key="option.id" :value="option.id">{{ option.name }}</option>
      </select>
    </div>
    <div class="field">
      <label for="title">Title</label>
      <input id="title" v-model="title" class="input" placeholder="Clean the bathroom" required>
    </div>
    <div class="field">
      <label for="description">Description</label>
      <textarea id="description" v-model="description" class="input" />
    </div>

    <div class="pair">
      <div class="field">
        <label for="deadline">Deadline</label>
        <input id="deadline" v-model="deadline" class="input" type="datetime-local">
      </div>
      <div class="field">
        <label for="weight">Weight</label>
        <input id="weight" v-model="weight" class="input" type="number" min="1">
        <p class="text-muted hint">Optional effort/points value.</p>
      </div>
    </div>

    <div class="toggles">
      <label class="radio option">
        <input v-model="requiresApproval" type="checkbox">
        <span class="dot square" />
        <span>
          Requires approval<br>
          <span class="text-muted hint">
            {{ store.isHierarchical
              ? 'An admin must approve completion in this household.'
              : 'Ignored in peer-to-peer households — kept for if the mode changes.' }}
          </span>
        </span>
      </label>
      <label class="radio option">
        <input v-model="isRecurring" type="checkbox">
        <span class="dot square" />
        <span>
          Recurring<br>
          <span class="text-muted hint">A fresh copy is created when this one is completed.</span>
        </span>
      </label>
      <div v-if="isRecurring" class="field interval">
        <label for="interval">Repeat every (days)</label>
        <input id="interval" v-model="intervalDays" class="input" type="number" min="1">
      </div>
    </div>

    <div class="actions">
      <button class="btn btn-primary" type="submit" :disabled="ui.busy">
        {{ editing ? 'Save changes' : 'Create task' }}
      </button>
      <button class="btn btn-secondary" type="button" @click="cancel">Cancel</button>
    </div>
  </form>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--space-6); max-width: 520px; }
h2 { margin: 0; }
.lede { margin: var(--space-2) 0 0; font-size: 14px; }
.pair { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: var(--space-4); }
.toggles { display: flex; flex-direction: column; gap: var(--space-3); }
.option { align-items: flex-start; }
.option .dot { margin-top: 3px; }
.square { border-radius: var(--radius-sm); }
.hint { margin: var(--space-1) 0 0; font-size: 13px; }
.interval { max-width: 200px; }
.actions { display: flex; gap: var(--space-3); }
</style>
