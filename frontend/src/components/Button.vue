<template>
  <button 
    :class="buttonClass" 
    :disabled="disabled"
    class="flex items-center justify-center font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline transition duration-300 ease-in-out">
    <span v-if="$slots.icon" class="mr-2">
      <slot name="icon"></slot>
    </span>
    <slot></slot>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps({
  variant: {
    type: String,
    default: 'primary',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
});

const buttonClass = computed(() => {
  if (props.disabled) {
    return 'bg-paper-disabled text-gray-500 cursor-not-allowed';
  }
  switch (props.variant) {
    case 'primary':
      return 'bg-paper-primary hover:bg-paper-primary-hover text-white';
    default:
      return 'bg-gray-500 hover:bg-gray-600 text-white';
  }
});
</script>
