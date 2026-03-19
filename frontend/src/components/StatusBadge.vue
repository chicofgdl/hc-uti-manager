<template>
  <span
    class="inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold leading-none"
    :class="badgeClass"
  >
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue';

type BedStatus = 'disponivel' | 'ocupado' | 'higienizacao' | 'desativado' | 'alta';

const props = defineProps<{
  status: BedStatus;
}>();

const statusConfig: Record<BedStatus, { label: string; className: string }> = {
  disponivel: {
    label: 'Disponivel',
    className: 'border border-emerald-200 bg-emerald-50 text-emerald-700',
  },
  ocupado: {
    label: 'Ocupado',
    className: 'border border-sky-200 bg-sky-50 text-sky-700',
  },
  higienizacao: {
    label: 'Higienizacao',
    className: 'border border-amber-200 bg-amber-50 text-amber-700',
  },
  desativado: {
    label: 'Desativado',
    className: 'border border-slate-200 bg-slate-100 text-slate-600',
  },
  alta: {
    label: 'Alta Solicitada',
    className: 'border border-rose-200 bg-rose-50 text-rose-700',
  },
};

const selectedConfig = computed(() => statusConfig[props.status]);
const label = computed(() => selectedConfig.value.label);
const badgeClass = computed(() => selectedConfig.value.className);
</script>
