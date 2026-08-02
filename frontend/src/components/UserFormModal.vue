<script setup>
import { reactive } from 'vue'
import Modal from './Modal.vue'

defineProps({
  isSubmitting: { type: Boolean, default: false },
})
const emit = defineEmits(['submit', 'cancel'])

const form = reactive({ email: '', password: '', is_admin: false })

function submit() {
  emit('submit', { email: form.email, password: form.password, is_admin: form.is_admin })
}
</script>

<template>
  <Modal title="Create User" subtitle="Add a new user account" @close="$emit('cancel')">
    <form class="modal-form" @submit.prevent="submit">
      <label>
        Email
        <input v-model="form.email" type="email" placeholder="name@company.com" required />
      </label>
      <label>
        Password
        <input v-model="form.password" type="password" placeholder="Enter a password" required />
      </label>
      <label class="checkbox-label">
        <input v-model="form.is_admin" type="checkbox" />
        Admin
      </label>
      <div class="modal-actions">
        <button type="button" class="btn btn-secondary" @click="$emit('cancel')">Cancel</button>
        <button type="submit" class="btn btn-primary" :disabled="isSubmitting">
          {{ isSubmitting ? 'Creating…' : 'Create User' }}
        </button>
      </div>
    </form>
  </Modal>
</template>
