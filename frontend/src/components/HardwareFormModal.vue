<script setup>
import { reactive } from 'vue'
import Modal from './Modal.vue'

const props = defineProps({
  mode: { type: String, default: 'add' }, // 'add' | 'edit'
  initialValue: { type: Object, default: null },
  isSubmitting: { type: Boolean, default: false },
})
const emit = defineEmits(['submit', 'cancel'])

const today = new Date().toISOString().slice(0, 10)

const form = reactive({
  name: props.initialValue?.name ?? '',
  brand: props.initialValue?.brand ?? '',
  purchase_date: props.initialValue?.purchase_date ?? '',
  notes: props.initialValue?.notes ?? '',
})

function submit() {
  emit('submit', {
    name: form.name,
    brand: form.brand,
    purchase_date: form.purchase_date || null,
    notes: form.notes || null,
  })
}
</script>

<template>
  <Modal
    :title="mode === 'edit' ? 'Edit Device' : 'Add New Device'"
    subtitle="Enter the details of the hardware device"
    @close="$emit('cancel')"
  >
    <form class="modal-form" @submit.prevent="submit">
      <label>
        Name
        <input v-model="form.name" placeholder="e.g., MacBook Pro 16&quot;" required />
      </label>
      <label>
        Brand
        <input v-model="form.brand" placeholder="e.g., Apple" required />
      </label>
      <label>
        Purchase Date
        <input v-model="form.purchase_date" type="date" :max="today" />
      </label>
      <label>
        Notes
        <textarea v-model="form.notes" rows="3" placeholder="Optional notes"></textarea>
      </label>
      <div class="modal-actions">
        <button type="button" class="btn btn-secondary" @click="$emit('cancel')">Cancel</button>
        <button type="submit" class="btn btn-primary" :disabled="isSubmitting">
          {{ isSubmitting ? 'Saving…' : mode === 'edit' ? 'Save Changes' : 'Add Device' }}
        </button>
      </div>
    </form>
  </Modal>
</template>
