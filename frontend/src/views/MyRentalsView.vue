<script setup>
import { onMounted, ref } from 'vue'
import { apiClient, ApiError } from '../api/client'
import StatusBadge from '../components/StatusBadge.vue'

const rentals = ref([])
const pendingRequests = ref([])
const isLoading = ref(true)
const error = ref('')
const returningId = ref(null)

async function loadAll() {
  isLoading.value = true
  error.value = ''
  try {
    const [rentalsData, requestsData] = await Promise.all([
      apiClient.get('/rentals/mine'),
      apiClient.get('/rental-requests/mine'),
    ])
    rentals.value = rentalsData
    pendingRequests.value = requestsData
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : 'Failed to load your rentals.'
  } finally {
    isLoading.value = false
  }
}

async function returnItem(rental) {
  returningId.value = rental.id
  error.value = ''
  try {
    await apiClient.post(`/hardware/${rental.hardware.id}/return`)
    await loadAll()
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : 'Failed to return this item.'
  } finally {
    returningId.value = null
  }
}

onMounted(loadAll)
</script>

<template>
  <div class="my-rentals">
    <h2>My Rentals</h2>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="isLoading">Loading…</p>

    <template v-else>
      <section v-if="pendingRequests.length > 0" class="pending-section">
        <h3>Pending Requests</h3>
        <table class="data-table pending-table">
          <thead>
            <tr>
              <th>Device Name</th>
              <th>Brand</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="request in pendingRequests" :key="request.id">
              <td>{{ request.hardware.name }}</td>
              <td>{{ request.hardware.brand }}</td>
              <td>Awaiting admin approval</td>
            </tr>
          </tbody>
        </table>
      </section>

      <table class="data-table rentals-table">
        <thead>
          <tr>
            <th>Device Name</th>
            <th>Brand</th>
            <th>Status</th>
            <th class="actions-col">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="rental in rentals" :key="rental.id">
            <td>{{ rental.hardware.name }}</td>
            <td>{{ rental.hardware.brand }}</td>
            <td><StatusBadge :status="rental.hardware.status" /></td>
            <td class="actions-col">
              <button
                class="btn btn-accent return-button"
                :disabled="returningId === rental.id"
                @click="returnItem(rental)"
              >
                {{ returningId === rental.id ? 'Returning…' : 'Return' }}
              </button>
            </td>
          </tr>
          <tr v-if="rentals.length === 0">
            <td colspan="4" class="empty-row">You don't have any active rentals.</td>
          </tr>
        </tbody>
      </table>
    </template>
  </div>
</template>

<style scoped>
.my-rentals h2 {
  margin-bottom: 1.5rem;
}

.pending-section {
  margin-bottom: 2rem;
}

.pending-section h3 {
  font-family: var(--font-heading);
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 0.75rem;
  color: var(--color-gray-500);
  text-transform: uppercase;
  letter-spacing: 0.02em;
}
</style>
