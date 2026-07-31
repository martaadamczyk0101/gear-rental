import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient } from '../api/client'

const STORAGE_KEY = 'hardware-rental-user'

function loadStoredUser() {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref(loadStoredUser())

  const isAuthenticated = computed(() => user.value !== null)
  const isAdmin = computed(() => user.value?.is_admin === true)

  async function login(email, password) {
    const loggedInUser = await apiClient.post('/auth/login', { email, password })
    user.value = loggedInUser
    localStorage.setItem(STORAGE_KEY, JSON.stringify(loggedInUser))
  }

  async function logout() {
    try {
      await apiClient.post('/auth/logout')
    } finally {
      user.value = null
      localStorage.removeItem(STORAGE_KEY)
    }
  }

  return { user, isAuthenticated, isAdmin, login, logout }
})
