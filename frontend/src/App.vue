<script setup>
import { onMounted, onUnmounted, watch } from 'vue'
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { useRentalRequestBadge } from './stores/rentalRequestBadge'
import ToastContainer from './components/ToastContainer.vue'

const authStore = useAuthStore()
const router = useRouter()
const badgeStore = useRentalRequestBadge()

async function handleLogout() {
  await authStore.logout()
  badgeStore.reset()
  router.push({ name: 'login' })
}

// Refresh immediately whenever the current session becomes an admin session -
// covers both a page load where the user is already logged in as admin, and
// the moment right after logging in (the login redirect happens without a
// full page reload, so waiting for the next poll tick left the badge blank
// for up to 25s).
watch(
  () => authStore.isAdmin,
  (isAdmin) => {
    if (isAdmin) badgeStore.refresh()
  },
  { immediate: true },
)

let pollTimer = null

onMounted(() => {
  pollTimer = setInterval(() => {
    if (authStore.isAdmin) badgeStore.refresh()
  }, 25000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div v-if="authStore.isAuthenticated" class="layout">
    <aside class="sidebar">
      <div class="brand">Hardware Manager</div>
      <nav class="nav-links">
        <RouterLink to="/">Hardware List</RouterLink>
        <RouterLink to="/my-rentals">My Rentals</RouterLink>
      </nav>

      <nav v-if="authStore.isAdmin" class="admin-nav">
        <div class="admin-nav-label">Admin</div>
        <RouterLink to="/admin" class="admin-link">
          Admin Panel
          <span v-if="badgeStore.pendingCount > 0" class="badge-count">{{ badgeStore.pendingCount }}</span>
        </RouterLink>
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
  <ToastContainer />
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
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  box-sizing: border-box;
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
.admin-nav {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
}
.admin-nav-label {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-gray-500);
  padding: 0 0.75rem 0.5rem;
}
.admin-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  text-decoration: none;
  color: var(--text);
  padding: 0.65rem 0.75rem;
  border-radius: 8px;
  font-weight: 500;
}
.admin-link.router-link-exact-active {
  background: var(--color-gray-100);
  font-weight: 700;
}
.badge-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 999px;
  background: var(--color-danger);
  color: var(--color-white);
  font-size: 0.75rem;
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
