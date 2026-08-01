<script setup>
import { onMounted, ref, watch } from 'vue'
import { apiClient, ApiError } from '../api/client'
import StatusBadge from '../components/StatusBadge.vue'

const hardware = ref([])
const isLoading = ref(true)
const error = ref('')
const rentingId = ref(null)

const statusFilter = ref('')
const searchTerm = ref('')
const sortBy = ref('name')
const sortDir = ref('asc')

async function loadHardware() {
  isLoading.value = true
  error.value = ''
  try {
    const params = new URLSearchParams({ sort_by: sortBy.value, sort_dir: sortDir.value })
    if (statusFilter.value) params.set('status', statusFilter.value)
    if (searchTerm.value) params.set('search', searchTerm.value)
    hardware.value = await apiClient.get(`/hardware?${params.toString()}`)
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : 'Failed to load hardware.'
  } finally {
    isLoading.value = false
  }
}

function toggleSort(column) {
  if (sortBy.value === column) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortBy.value = column
    sortDir.value = 'asc'
  }
}

function sortIndicator(column) {
  if (sortBy.value !== column) return ''
  return sortDir.value === 'asc' ? '▲' : '▼'
}

async function rent(item) {
  rentingId.value = item.id
  error.value = ''
  try {
    await apiClient.post(`/hardware/${item.id}/rent`)
    await loadHardware()
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : 'Failed to rent this item.'
  } finally {
    rentingId.value = null
  }
}

watch([statusFilter, sortBy, sortDir], loadHardware)

let searchDebounce
watch(searchTerm, () => {
  clearTimeout(searchDebounce)
  searchDebounce = setTimeout(loadHardware, 300)
})

onMounted(loadHardware)
</script>

<template>
  <div class="dashboard">
    <div class="header-row">
      <h2>Hardware Dashboard</h2>
    </div>

    <div class="filters">
      <input v-model="searchTerm" type="search" placeholder="Search by name…" class="search-input" />
      <select v-model="statusFilter" class="status-select">
        <option value="">All statuses</option>
        <option value="available">Available</option>
        <option value="in use">In Use</option>
        <option value="in repair">In Repair</option>
      </select>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="isLoading">Loading…</p>

    <table v-else class="data-table hardware-table">
      <thead>
        <tr>
          <th @click="toggleSort('name')">Device Name {{ sortIndicator('name') }}</th>
          <th @click="toggleSort('brand')">Brand {{ sortIndicator('brand') }}</th>
          <th @click="toggleSort('purchase_date')">Purchase Date {{ sortIndicator('purchase_date') }}</th>
          <th @click="toggleSort('status')">Status {{ sortIndicator('status') }}</th>
          <th class="actions-col">Action</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in hardware" :key="item.id">
          <td>{{ item.name }}</td>
          <td>{{ item.brand }}</td>
          <td>{{ item.purchase_date || '—' }}</td>
          <td><StatusBadge :status="item.status" /></td>
          <td class="actions-col">
            <button
              v-if="item.status === 'available'"
              class="btn btn-primary rent-button"
              :disabled="rentingId === item.id"
              @click="rent(item)"
            >
              {{ rentingId === item.id ? 'Renting…' : 'Rent' }}
            </button>
            <button v-else class="btn btn-primary rent-button" disabled>Rent</button>
          </td>
        </tr>
        <tr v-if="hardware.length === 0">
          <td colspan="5" class="empty-row">No hardware matches your filters.</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.header-row {
  margin-bottom: 1.5rem;
}

.filters {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.search-input,
.status-select {
  padding: 0.6rem 0.9rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
  color: var(--text);
  font-size: 0.95rem;
}

.search-input {
  flex: 1;
  max-width: 320px;
}

.hardware-table th {
  cursor: pointer;
  user-select: none;
}
</style>
