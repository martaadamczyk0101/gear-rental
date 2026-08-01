<script setup>
import { onMounted, reactive, ref } from 'vue'
import { apiClient, ApiError } from '../api/client'
import StatusBadge from '../components/StatusBadge.vue'

const hardware = ref([])
const isLoadingHardware = ref(true)
const hardwareError = ref('')

const showAddForm = ref(false)
const isCreatingHardware = ref(false)
const newHardware = reactive({ name: '', brand: '', purchase_date: '', notes: '' })

const togglingId = ref(null)
const deletingId = ref(null)

const editingNotesId = ref(null)
const notesDraft = ref('')
const savingNotes = ref(false)

const newUser = reactive({ email: '', password: '', is_admin: false })
const isCreatingUser = ref(false)
const userError = ref('')
const userSuccess = ref('')

async function loadHardware() {
  isLoadingHardware.value = true
  hardwareError.value = ''
  try {
    hardware.value = await apiClient.get('/hardware')
  } catch (err) {
    hardwareError.value = err instanceof ApiError ? err.message : 'Failed to load hardware.'
  } finally {
    isLoadingHardware.value = false
  }
}

async function createHardware() {
  isCreatingHardware.value = true
  hardwareError.value = ''
  try {
    await apiClient.post('/hardware', {
      name: newHardware.name,
      brand: newHardware.brand,
      purchase_date: newHardware.purchase_date || null,
      notes: newHardware.notes || null,
    })
    newHardware.name = ''
    newHardware.brand = ''
    newHardware.purchase_date = ''
    newHardware.notes = ''
    showAddForm.value = false
    await loadHardware()
  } catch (err) {
    hardwareError.value = err instanceof ApiError ? err.message : 'Failed to create hardware.'
  } finally {
    isCreatingHardware.value = false
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

function startNotesEdit(item) {
  editingNotesId.value = item.id
  notesDraft.value = item.notes || ''
}

function cancelNotesEdit() {
  editingNotesId.value = null
  notesDraft.value = ''
}

async function saveNotes(item) {
  savingNotes.value = true
  hardwareError.value = ''
  try {
    await apiClient.patch(`/hardware/${item.id}/notes`, { notes: notesDraft.value || null })
    editingNotesId.value = null
    await loadHardware()
  } catch (err) {
    hardwareError.value = err instanceof ApiError ? err.message : 'Failed to save notes.'
  } finally {
    savingNotes.value = false
  }
}

async function createUser() {
  isCreatingUser.value = true
  userError.value = ''
  userSuccess.value = ''
  try {
    const user = await apiClient.post('/users', {
      email: newUser.email,
      password: newUser.password,
      is_admin: newUser.is_admin,
    })
    userSuccess.value = `User ${user.email} created${user.is_admin ? ' (admin)' : ''}.`
    newUser.email = ''
    newUser.password = ''
    newUser.is_admin = false
  } catch (err) {
    userError.value = err instanceof ApiError ? err.message : 'Failed to create user.'
  } finally {
    isCreatingUser.value = false
  }
}

onMounted(loadHardware)
</script>

<template>
  <div class="admin">
    <section class="panel">
      <div class="panel-header">
        <h2>Hardware Management</h2>
        <button class="btn btn-primary" @click="showAddForm = !showAddForm">
          {{ showAddForm ? 'Cancel' : '+ Add New Device' }}
        </button>
      </div>

      <form v-if="showAddForm" class="add-form" @submit.prevent="createHardware">
        <input v-model="newHardware.name" placeholder="Device name" required />
        <input v-model="newHardware.brand" placeholder="Brand" required />
        <input v-model="newHardware.purchase_date" type="date" />
        <input v-model="newHardware.notes" placeholder="Notes (optional)" />
        <button type="submit" class="btn btn-primary" :disabled="isCreatingHardware">
          {{ isCreatingHardware ? 'Adding…' : 'Add device' }}
        </button>
      </form>

      <p v-if="hardwareError" class="error">{{ hardwareError }}</p>
      <p v-if="isLoadingHardware">Loading…</p>

      <table v-else class="data-table admin-table">
        <thead>
          <tr>
            <th>Device Name</th>
            <th>Brand</th>
            <th>Purchase Date</th>
            <th>Status</th>
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
            <td class="notes-cell">
              <div v-if="editingNotesId === item.id" class="notes-edit">
                <textarea v-model="notesDraft" rows="2"></textarea>
                <div class="notes-edit-actions">
                  <button type="button" class="link-button" :disabled="savingNotes" @click="saveNotes(item)">
                    Save
                  </button>
                  <button type="button" class="link-button" @click="cancelNotesEdit">Cancel</button>
                </div>
              </div>
              <div v-else class="notes-display" @click="startNotesEdit(item)">
                {{ item.notes || 'Add notes…' }}
              </div>
            </td>
            <td class="actions-col">
              <button
                class="icon-button"
                type="button"
                :disabled="item.status === 'in use' || togglingId === item.id"
                :title="item.status === 'in repair' ? 'Mark available' : 'Send to repair'"
                @click="toggleRepair(item)"
              >
                🔧
              </button>
              <button
                class="icon-button danger"
                type="button"
                :disabled="item.status === 'in use' || deletingId === item.id"
                title="Delete"
                @click="deleteHardware(item)"
              >
                🗑
              </button>
            </td>
          </tr>
          <tr v-if="hardware.length === 0">
            <td colspan="6" class="empty-row">No hardware yet.</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="panel">
      <h2>Create User</h2>
      <form class="user-form" @submit.prevent="createUser">
        <input v-model="newUser.email" type="email" placeholder="Email" required />
        <input v-model="newUser.password" type="password" placeholder="Password" required />
        <label class="checkbox-label">
          <input v-model="newUser.is_admin" type="checkbox" />
          Admin
        </label>
        <button type="submit" class="btn btn-primary" :disabled="isCreatingUser">
          {{ isCreatingUser ? 'Creating…' : 'Create user' }}
        </button>
      </form>
      <p v-if="userError" class="error">{{ userError }}</p>
      <p v-if="userSuccess" class="success">{{ userSuccess }}</p>
    </section>
  </div>
</template>

<style scoped>
.admin {
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
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

.add-form,
.user-form {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: var(--surface);
  border-radius: 10px;
}

.add-form input,
.user-form input {
  padding: 0.55rem 0.8rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg);
  color: var(--text);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.9rem;
}

.admin-table td {
  vertical-align: top;
}

.notes-cell {
  max-width: 220px;
}

.notes-display {
  cursor: pointer;
  color: var(--color-gray-500);
  min-height: 1.2em;
}
.notes-display:hover {
  color: var(--text);
}

.notes-edit {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.notes-edit textarea {
  padding: 0.4rem;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  color: var(--text);
  resize: vertical;
}
.notes-edit-actions {
  display: flex;
  gap: 0.75rem;
}

.link-button {
  background: none;
  border: none;
  padding: 0;
  color: var(--color-teal);
  font-weight: 600;
  cursor: pointer;
}
.link-button:disabled {
  color: var(--color-gray-500);
  cursor: not-allowed;
}

.icon-button {
  border: 1px solid var(--border);
  background: var(--bg);
  border-radius: 6px;
  padding: 0.4rem 0.6rem;
  margin-left: 0.4rem;
  cursor: pointer;
}
.icon-button:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}
.icon-button.danger:hover:not(:disabled) {
  border-color: var(--color-danger);
}
</style>
