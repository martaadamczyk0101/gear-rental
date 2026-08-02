<script setup>
import { computed, onMounted, ref, watch } from 'vue'
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

const aiQuery = ref('')
const aiResults = ref([])
const aiActive = ref(false)
const isAiSearching = ref(false)
const aiError = ref('')

const visibleHardware = computed(() => (aiActive.value ? aiResults.value : hardware.value))

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
  if (aiActive.value) return
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
    if (aiActive.value) {
      await runAiSearch()
    } else {
      await loadHardware()
    }
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : 'Failed to rent this item.'
  } finally {
    rentingId.value = null
  }
}

async function runAiSearch() {
  const query = aiQuery.value.trim()
  if (!query) return
  isAiSearching.value = true
  aiError.value = ''
  try {
    aiResults.value = await apiClient.get(`/hardware/semantic-search?q=${encodeURIComponent(query)}`)
    aiActive.value = true
  } catch (err) {
    aiError.value = err instanceof ApiError ? err.message : 'Semantic search failed.'
  } finally {
    isAiSearching.value = false
  }
}

function clearAiSearch() {
  aiActive.value = false
  aiResults.value = []
  aiQuery.value = ''
  aiError.value = ''
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

    <form class="ai-search" @submit.prevent="runAiSearch">
      <span class="ai-icon">🔍</span>
      <input
        v-model="aiQuery"
        type="text"
        placeholder="Ask AI…"
        class="ai-input"
      />
      <button
        v-if="aiActive"
        type="button"
        class="btn ai-clear-button"
        @click="clearAiSearch"
      >
        Clear
      </button>
      <button type="submit" class="ai-submit-button" :disabled="isAiSearching || !aiQuery.trim()">
        {{ isAiSearching ? 'Searching…' : '✨' }}
      </button>
    </form>
    <p v-if="aiError" class="error">{{ aiError }}</p>
    <p v-if="aiActive" class="ai-results-note">
      Showing AI matches for “{{ aiQuery }}” — <a href="#" @click.prevent="clearAiSearch">back to browsing</a>
    </p>

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
        <tr v-for="item in visibleHardware" :key="item.id">
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
        <tr v-if="visibleHardware.length === 0">
          <td colspan="5" class="empty-row">
            {{ aiActive ? 'No hardware matched that request.' : 'No hardware matches your filters.' }}
          </td>
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

.ai-search {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.7rem 1rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  margin-bottom: 0.75rem;
}

.ai-icon {
  color: var(--color-gray-500);
}

.ai-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 0.95rem;
  color: var(--text);
  outline: none;
}

.ai-submit-button {
  border: none;
  background: none;
  font-size: 1.2rem;
  line-height: 1;
  cursor: pointer;
  color: var(--color-teal);
  padding: 0.25rem;
}

.ai-submit-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.ai-clear-button {
  padding: 0.4rem 0.9rem;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--text);
  font-weight: 600;
  cursor: pointer;
}

.ai-results-note {
  margin: 0 0 1.5rem;
  font-size: 0.9rem;
  color: var(--color-gray-500);
}

.ai-results-note a {
  color: var(--color-teal);
  font-weight: 600;
}
</style>
