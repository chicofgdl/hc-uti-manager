<template>
  <span
    :class="[
      'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
      variantClass,
    ]"
  >
    <slot/>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue';

type Variant = 'default' | 'secondary' | 'destructive' | 'outline';

const props = defineProps<{
  variant?: Variant;
}>();

const variantClass = computed(() => {
  switch (props.variant) {
    case 'secondary':
      return 'border-slate-200 bg-slate-100 text-slate-700 hover:bg-slate-200';
    case 'destructive':
      return 'border-rose-200 bg-rose-100 text-rose-700 hover:bg-rose-200';
    case 'outline':
      return 'border-slate-200 bg-white text-slate-700';
    case 'default':
    default:
      return 'border-sky-200 bg-sky-50 text-sky-700 hover:bg-sky-100';
  }
});
</script>
