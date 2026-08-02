<script setup>
defineProps({ size: { type: [Number, String], default: 18 } })
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.5"
    stroke-linecap="round"
    stroke-linejoin="round"
  >
    <line x1="12" y1="3" x2="12" y2="21" />
    <line x1="4.5" y1="7.5" x2="19.5" y2="16.5" />
    <line x1="19.5" y1="7.5" x2="4.5" y2="16.5" />
  </svg>
</template>
