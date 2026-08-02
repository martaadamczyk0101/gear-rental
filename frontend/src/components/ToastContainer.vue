<script setup>
import { useToastStore } from '../stores/toast'
import IconCheck from './icons/IconCheck.vue'

const toastStore = useToastStore()
</script>

<template>
  <div class="toast-container">
    <div v-for="toast in toastStore.toasts" :key="toast.id" class="toast">
      <span class="toast-icon"><IconCheck :size="13" /></span>
      <span>{{ toast.message }}</span>
    </div>
  </div>
</template>

<style scoped>
.toast-container {
  position: fixed;
  bottom: 1.5rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  z-index: 200;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  background: var(--bg);
  border-radius: 12px;
  padding: 0.8rem 1.25rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  font-weight: 500;
  white-space: nowrap;
}

.toast-icon {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--color-black);
  color: var(--color-white);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  flex-shrink: 0;
}
</style>
