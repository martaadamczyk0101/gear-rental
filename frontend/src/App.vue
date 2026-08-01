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
  <div v-if="authStore.isAuthenticated" class="layout">
    <aside class="sidebar">
      <div class="brand">Hardware Manager</div>
      <nav class="nav-links">
        <RouterLink to="/">Dashboard</RouterLink>
        <RouterLink to="/my-rentals">My Rentals</RouterLink>
        <RouterLink v-if="authStore.isAdmin" to="/admin">Admin Panel</RouterLink>
      </nav>
      <div class="sidebar-footer">
        <span class="user-email">{{ authStore.user.email }}</span>
        <button class="logout-button" @click="handleLogout">Log out</button>
      </div>
    </aside>
    <main class="content">
      <RouterView />
    </main>
  </div>
  <RouterView v-else />
</template>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
}
.sidebar {
  width: 240px;
  flex-shrink: 0;
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 1.5rem 1rem;
}
.brand {
  font-family: var(--font-heading);
  font-weight: 800;
  font-size: 1.15rem;
  padding: 0 0.75rem 1.5rem;
}
.nav-links {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.nav-links a {
  text-decoration: none;
  color: var(--text);
  padding: 0.65rem 0.75rem;
  border-radius: 8px;
  font-weight: 500;
}
.nav-links a.router-link-exact-active {
  background: var(--color-gray-100);
  font-weight: 700;
}
.sidebar-footer {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem;
  border-top: 1px solid var(--border);
}
.user-email {
  font-size: 0.85rem;
  color: var(--color-gray-500);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.logout-button {
  padding: 0.5rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg);
  color: var(--text);
  cursor: pointer;
  font-weight: 600;
}
.content {
  flex: 1;
  padding: 2rem;
  overflow-x: auto;
}
</style>
