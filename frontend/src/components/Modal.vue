<script setup>
import IconClose from './icons/IconClose.vue'

defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
})
defineEmits(['close'])
</script>

<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-card">
      <div class="modal-header">
        <div>
          <h2>{{ title }}</h2>
          <p v-if="subtitle" class="modal-subtitle">{{ subtitle }}</p>
        </div>
        <button type="button" class="modal-close" aria-label="Close" @click="$emit('close')">
          <IconClose :size="16" />
        </button>
      </div>
      <div class="modal-body">
        <slot />
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 1rem;
}

.modal-card {
  background: var(--bg);
  border-radius: 16px;
  width: 100%;
  max-width: 440px;
  max-height: 90vh;
  overflow-y: auto;
  padding: 1.75rem;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
}

.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 1.25rem;
}

.modal-header h2 {
  font-size: 1.4rem;
}

.modal-subtitle {
  margin: 0.35rem 0 0;
  color: var(--color-gray-500);
  font-size: 0.9rem;
}

.modal-close {
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: none;
  line-height: 1;
  cursor: pointer;
  color: var(--color-gray-500);
  padding: 0.25rem;
}

.modal-close:hover {
  color: var(--text);
}
</style>
