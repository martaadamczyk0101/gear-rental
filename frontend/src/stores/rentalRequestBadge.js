import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiClient } from '../api/client'

export const useRentalRequestBadge = defineStore('rentalRequestBadge', () => {
  const pendingCount = ref(0)

  async function refresh() {
    try {
      const result = await apiClient.get('/rental-requests/pending-count')
      pendingCount.value = result.pending
    } catch {
      // Non-critical - the badge just won't update this tick.
    }
  }

  function reset() {
    pendingCount.value = 0
  }

  return { pendingCount, refresh, reset }
})
