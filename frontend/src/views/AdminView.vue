<script setup>
import { onMounted, ref, watch } from 'vue'
import { apiClient, ApiError } from '../api/client'
import StatusBadge from '../components/StatusBadge.vue'
import HardwareFormModal from '../components/HardwareFormModal.vue'
import UserFormModal from '../components/UserFormModal.vue'
import IconPencil from '../components/icons/IconPencil.vue'
import IconWrench from '../components/icons/IconWrench.vue'
import IconTrash from '../components/icons/IconTrash.vue'
import { useRentalRequestBadge } from '../stores/rentalRequestBadge'

const badgeStore = useRentalRequestBadge()

const hardware = ref([])
const isLoadingHardware = ref(true)
const hardwareError = ref('')

const statusFilter = ref('')
const searchTerm = ref('')
const sortBy = ref('name')
const sortDir = ref('asc')

const showHardwareModal = ref(false)
const editingItem = ref(null)
const isSavingHardware = ref(false)

const togglingId = ref(null)
const deletingId = ref(null)

const showUserModal = ref(false)
const isCreatingUser = ref(false)
const userError = ref('')
const userSuccess = ref('')

const pendingRequests = ref([])
const isLoadingRequests = ref(true)
const requestsError = ref('')
const decidingRequestId = ref(null)

async function loadHardware() {
  isLoadingHardware.value = true
  hardwareError.value = ''
  try {
    const params = new URLSearchParams({ sort_by: sortBy.value, sort_dir: sortDir.value })
    if (statusFilter.value) params.set('status', statusFilter.value)
    if (searchTerm.value) params.set('search', searchTerm.value)
    hardware.value = await apiClient.get(`/hardware?${params.toString()}`)
  } catch (err) {
    hardwareError.value = err instanceof ApiError ? err.message : 'Failed to load hardware.'
  } finally {
    isLoadingHardware.value = false
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

watch([statusFilter, sortBy, sortDir], loadHardware)

let searchDebounce
watch(searchTerm, () => {
  clearTimeout(searchDebounce)
  searchDebounce = setTimeout(loadHardware, 300)
})

function openAddModal() {
  editingItem.value = null
  showHardwareModal.value = true
}

function openEditModal(item) {
  editingItem.value = item
  showHardwareModal.value = true
}

function closeHardwareModal() {
  showHardwareModal.value = false
  editingItem.value = null
}

async function submitHardwareForm(payload) {
  isSavingHardware.value = true
  hardwareError.value = ''
  try {
    if (editingItem.value) {
      await apiClient.patch(`/hardware/${editingItem.value.id}`, payload)
    } else {
      await apiClient.post('/hardware', payload)
    }
    closeHardwareModal()
    await loadHardware()
  } catch (err) {
    hardwareError.value = err instanceof ApiError ? err.message : 'Failed to save hardware.'
  } finally {
    isSavingHardware.value = false
  }
}

async function toggleRepair(item) {
  togglingId.value = item.id
  hardwareError.value = ''
  try {
    await apiClient.patch(`/hardware/${item.id}/repair-toggle`)
    await loadHardware()
  } catch (err) {
    hardwareError.value = err instanceof ApiError ? err.message : 'Failed to update repair status.'
  } finally {
    togglingId.value = null
  }
}

async function deleteHardware(item) {
  if (!confirm(`Delete "${item.name}"? This cannot be undone.`)) return
  deletingId.value = item.id
  hardwareError.value = ''
  try {
    await apiClient.delete(`/hardware/${item.id}`)
    await loadHardware()
  } catch (err) {
    hardwareError.value = err instanceof ApiError ? err.message : 'Failed to delete hardware.'
  } finally {
    deletingId.value = null
  }
}

function openUserModal() {
  userError.value = ''
  userSuccess.value = ''
  showUserModal.value = true
}

async function submitUserForm(payload) {
  isCreatingUser.value = true
  userError.value = ''
  try {
    const user = await apiClient.post('/users', payload)
    userSuccess.value = `User ${user.email} created${user.is_admin ? ' (admin)' : ''}.`
    showUserModal.value = false
  } catch (err) {
    userError.value = err instanceof ApiError ? err.message : 'Failed to create user.'
  } finally {
    isCreatingUser.value = false
  }
}

async function loadRequests() {
  isLoadingRequests.value = true
  requestsError.value = ''
  try {
    pendingRequests.value = await apiClient.get('/rental-requests')
  } catch (err) {
    requestsError.value = err instanceof ApiError ? err.message : 'Failed to load rental requests.'
  } finally {
    isLoadingRequests.value = false
  }
}

function formatDateTime(iso) {
  return new Date(iso).toLocaleString()
}

async function approveRequest(request) {
  decidingRequestId.value = request.id
  requestsError.value = ''
  try {
    await apiClient.post(`/rental-requests/${request.id}/approve`)
    await Promise.all([loadRequests(), loadHardware(), badgeStore.refresh()])
  } catch (err) {
    requestsError.value = err instanceof ApiError ? err.message : 'Failed to approve request.'
  } finally {
    decidingRequestId.value = null
  }
}

async function rejectRequest(request) {
  decidingRequestId.value = request.id
  requestsError.value = ''
  try {
    await apiClient.post(`/rental-requests/${request.id}/reject`)
    await Promise.all([loadRequests(), badgeStore.refresh()])
  } catch (err) {
    requestsError.value = err instanceof ApiError ? err.message : 'Failed to reject request.'
  } finally {
    decidingRequestId.value = null
  }
}

onMounted(() => {
  loadHardware()
  loadRequests()
})
</script>

<template>
  <div class="admin">
    <section class="panel">
      <h2>Rental Requests</h2>
      <p v-if="requestsError" class="error">{{ requestsError }}</p>
      <p v-if="isLoadingRequests">Loading…</p>

      <table v-else class="data-table requests-table">
        <thead>
          <tr>
            <th>Device Name</th>
            <th>Brand</th>
            <th>Requested By</th>
            <th>Requested At</th>
            <th class="actions-col">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="request in pendingRequests" :key="request.id">
            <td>{{ request.hardware.name }}</td>
            <td>{{ request.hardware.brand }}</td>
            <td>{{ request.user.email }}</td>
            <td>{{ formatDateTime(request.requested_at) }}</td>
            <td class="actions-col">
              <button
                class="btn btn-primary"
                :disabled="decidingRequestId === request.id"
                @click="approveRequest(request)"
              >
                Approve
              </button>
              <button
                class="btn btn-secondary"
                :disabled="decidingRequestId === request.id"
                @click="rejectRequest(request)"
              >
                Reject
              </button>
            </td>
          </tr>
          <tr v-if="pendingRequests.length === 0">
            <td colspan="5" class="empty-row">No pending requests.</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="panel">
      <div class="panel-header">
        <h2>Hardware Management</h2>
        <button class="btn btn-primary" @click="openAddModal">+ Add New Device</button>
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

      <p v-if="hardwareError" class="error">{{ hardwareError }}</p>
      <p v-if="isLoadingHardware">Loading…</p>

      <table v-else class="data-table admin-table">
        <thead>
          <tr>
            <th @click="toggleSort('name')">Device Name {{ sortIndicator('name') }}</th>
            <th @click="toggleSort('brand')">Brand {{ sortIndicator('brand') }}</th>
            <th @click="toggleSort('purchase_date')">Purchase Date {{ sortIndicator('purchase_date') }}</th>
            <th @click="toggleSort('status')">Status {{ sortIndicator('status') }}</th>
            <th>Notes</th>
            <th class="actions-col">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in hardware" :key="item.id">
            <td>{{ item.name }}</td>
            <td>{{ item.brand }}</td>
            <td>{{ item.purchase_date || '—' }}</td>
            <td><StatusBadge :status="item.status" /></td>
            <td class="notes-cell">{{ item.notes || '—' }}</td>
            <td class="actions-col">
              <button class="icon-button" type="button" title="Edit" @click="openEditModal(item)">
                <IconPencil :size="16" />
              </button>
              <button
                class="icon-button"
                type="button"
                :disabled="item.status === 'in use' || togglingId === item.id"
                :title="item.status === 'in repair' ? 'Mark available' : 'Send to repair'"
                @click="toggleRepair(item)"
              >
                <IconWrench :size="16" />
              </button>
              <button
                class="icon-button danger"
                type="button"
                :disabled="item.status === 'in use' || deletingId === item.id"
                title="Delete"
                @click="deleteHardware(item)"
              >
                <IconTrash :size="16" />
              </button>
            </td>
          </tr>
          <tr v-if="hardware.length === 0">
            <td colspan="6" class="empty-row">No hardware matches your filters.</td>
          </tr>
        </tbody>
      </table>

      <HardwareFormModal
        v-if="showHardwareModal"
        :mode="editingItem ? 'edit' : 'add'"
        :initial-value="editingItem"
        :is-submitting="isSavingHardware"
        @submit="submitHardwareForm"
        @cancel="closeHardwareModal"
      />
    </section>

    <section class="panel">
      <div class="panel-header">
        <h2>Create User</h2>
        <button class="btn btn-primary" @click="openUserModal">+ Create User</button>
      </div>
      <p v-if="userError" class="error">{{ userError }}</p>
      <p v-if="userSuccess" class="success">{{ userSuccess }}</p>

      <UserFormModal
        v-if="showUserModal"
        :is-submitting="isCreatingUser"
        @submit="submitUserForm"
        @cancel="showUserModal = false"
      />
    </section>
  </div>
</template>

<style scoped>
.admin {
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
  font-size: 0.9rem;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.panel h2 {
  margin-bottom: 1.5rem;
}
.panel-header h2 {
  margin-bottom: 0;
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
  font-size: 0.9rem;
}

.status-select {
  padding-right: 2rem;
}

.search-input {
  flex: 1;
  max-width: 320px;
}

.admin-table th {
  cursor: pointer;
  user-select: none;
}

.admin-table td {
  vertical-align: top;
}

.notes-cell {
  max-width: 220px;
  color: var(--color-gray-500);
}

.icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--text);
  border-radius: 6px;
  padding: 0.4rem 0.5rem;
  margin-left: 0.4rem;
  cursor: pointer;
}
.icon-button:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}
.icon-button.danger:hover:not(:disabled) {
  border-color: var(--color-danger);
  color: var(--color-danger);
}

.requests-table .actions-col button + button {
  margin-left: 0.5rem;
}
</style>
