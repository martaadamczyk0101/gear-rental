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
    <form class="login-card" @submit.prevent="handleSubmit">
      <div class="icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M21 8 12 3 3 8l9 5 9-5Z" />
          <path d="M3 8v8l9 5 9-5V8" />
          <path d="M12 13v8" />
        </svg>
      </div>
      <h1>Welcome back</h1>
      <p class="subtitle">Sign in to your account</p>

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
  background: var(--surface);
}
.login-card {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 340px;
  padding: 2.5rem;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 16px;
}
.icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: var(--color-gray-100);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-black);
  margin-bottom: 0.5rem;
}
.icon svg {
  width: 24px;
  height: 24px;
}
h1 {
  font-size: 1.5rem;
}
.subtitle {
  margin: 0.25rem 0 0.5rem;
  color: var(--color-gray-500);
}
label {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.9rem;
  font-weight: 500;
}
input {
  padding: 0.7rem 0.9rem;
  font-size: 1rem;
  font-family: var(--font-body);
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--color-gray-50);
  color: var(--text);
}
input:focus {
  outline: 2px solid var(--color-teal);
  outline-offset: 1px;
}
button {
  padding: 0.75rem;
  font-size: 1rem;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  background: var(--color-black);
  color: var(--color-white);
  cursor: pointer;
  margin-top: 0.5rem;
}
button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.error {
  color: var(--color-danger);
  font-size: 0.9rem;
  margin: 0;
}
</style>
