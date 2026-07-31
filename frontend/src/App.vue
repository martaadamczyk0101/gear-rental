<script setup>
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()
const router = useRouter()

async function handleLogout() {
  await authStore.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <nav v-if="authStore.isAuthenticated" class="navbar">
    <RouterLink to="/">Dashboard</RouterLink>
    <RouterLink to="/my-rentals">My Rentals</RouterLink>
    <RouterLink v-if="authStore.isAdmin" to="/admin">Admin</RouterLink>
    <span class="spacer" />
    <span>{{ authStore.user.email }}</span>
    <button @click="handleLogout">Log out</button>
  </nav>
  <main>
    <RouterView />
  </main>
</template>

<style scoped>
.navbar {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-bottom: 1px solid #ddd;
}
.navbar a {
  text-decoration: none;
  color: inherit;
}
.navbar a.router-link-exact-active {
  font-weight: bold;
}
.spacer {
  flex: 1;
}
main {
  padding: 1.5rem;
}
</style>
