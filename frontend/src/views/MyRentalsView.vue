<script setup>
import { onMounted, ref } from 'vue'
import { apiClient, ApiError } from '../api/client'
import StatusBadge from '../components/StatusBadge.vue'

const rentals = ref([])
const isLoading = ref(true)
const error = ref('')
const returningId = ref(null)

async function loadRentals() {
  isLoading.value = true
  error.value = ''
  try {
    rentals.value = await apiClient.get('/rentals/mine')
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
    await loadRentals()
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : 'Failed to return this item.'
  } finally {
    returningId.value = null
  }
}

onMounted(loadRentals)
</script>

<template>
  <div class="my-rentals">
    <h2>My Rentals</h2>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="isLoading">Loading…</p>

    <table v-else class="data-table rentals-table">
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
  </div>
</template>

<style scoped>
.my-rentals h2 {
  margin-bottom: 1.5rem;
}
</style>
