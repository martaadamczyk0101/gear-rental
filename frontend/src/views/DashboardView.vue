<script setup>
import { onMounted, ref } from 'vue'
import { apiClient } from '../api/client'

// Placeholder for now: just proves the X-User-Id auth plumbing works end to
// end. The real hardware table with filtering/sorting is built in the next
// phase.
const me = ref(null)
const error = ref('')

onMounted(async () => {
  try {
    me.value = await apiClient.get('/auth/me')
  } catch (err) {
    error.value = err.message
  }
})
</script>

<template>
  <div>
    <h2>Dashboard</h2>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-else-if="me">
      Logged in as <strong>{{ me.email }}</strong> ({{ me.is_admin ? 'admin' : 'user' }}).
    </p>
    <p>The hardware list with filtering and sorting will be built here in the next phase.</p>
  </div>
</template>

<style scoped>
.error {
  color: #c0392b;
}
</style>
