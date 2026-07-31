<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ApiError } from '../api/client'

const email = ref('')
const password = ref('')
const error = ref('')
const isSubmitting = ref(false)

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

async function handleSubmit() {
  error.value = ''
  isSubmitting.value = true
  try {
    await authStore.login(email.value, password.value)
    router.push(route.query.redirect || '/')
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : 'Something went wrong, please try again.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <form class="login-form" @submit.prevent="handleSubmit">
      <h1>Hardware Rental</h1>
      <label>
        Email
        <input v-model="email" type="email" required autofocus />
      </label>
      <label>
        Password
        <input v-model="password" type="password" required />
      </label>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" :disabled="isSubmitting">
        {{ isSubmitting ? 'Logging in…' : 'Log in' }}
      </button>
    </form>
  </div>
</template>

<style scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}
.login-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 320px;
  padding: 2rem;
  border: 1px solid #ddd;
  border-radius: 8px;
}
label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.9rem;
}
input {
  padding: 0.5rem;
  font-size: 1rem;
}
button {
  padding: 0.6rem;
  font-size: 1rem;
  cursor: pointer;
}
.error {
  color: #c0392b;
  font-size: 0.9rem;
}
</style>
