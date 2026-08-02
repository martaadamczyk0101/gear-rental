<script setup>
defineProps({
  status: {
    type: String,
    required: true,
  },
})

const LABELS = {
  available: 'Available',
  'in use': 'In Use',
  'in repair': 'In Repair',
}
</script>

<template>
  <span class="badge" :class="`badge--${status.replace(' ', '-')}`">
    {{ LABELS[status] || status }}
  </span>
</template>

<style scoped>
.badge {
  box-sizing: border-box;
  display: inline-block;
  width: 80px;
  padding: 0.3rem 0.4rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
  text-align: center;
}

.badge--available {
  background: var(--color-black);
  color: var(--color-white);
}

.badge--in-use {
  background: var(--color-gray-200);
  color: var(--text);
}

.badge--in-repair {
  background: var(--color-danger);
  color: var(--color-white);
}
</style>
