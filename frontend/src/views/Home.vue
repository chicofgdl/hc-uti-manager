<template>
  <section class="space-y-6">
    <div class="space-y-3 mb-4">
      <div class="flex items-center justify-between">
        <h2 class="text-3xl font-bold text-slate-900">Leitos da UTI</h2>
        <UiButton size="sm" variant="outline" @click="reload">
          Atualizar
        </UiButton>
      </div>
      <p class="text-sm text-slate-600">
        Esta tela foi adaptada ao contrato atual do YAML usando `GET /leitos`. A alteracao de disponibilidade ainda depende de endpoint no backend.
      </p>
      <p v-if="!isIcu" class="text-sm text-amber-700">
        A conta atual não possui permissão UTI. Esta tela fica em modo leitura.
      </p>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p class="text-sm font-medium text-slate-600">Total de leitos</p>
          <p class="mt-1 text-3xl font-bold text-slate-900">{{ totalBeds }}</p>
        </div>
        <div class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p class="text-sm font-medium text-slate-600">Com alta solicitada e sem próximo paciente</p>
          <p class="mt-1 text-3xl font-bold text-emerald-700">{{ bedsStore.availableCount }}</p>
        </div>
        <div class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p class="text-sm font-medium text-slate-600">Com próximo paciente definido</p>
          <p class="mt-1 text-3xl font-bold text-blue-700">{{ reservedBeds }}</p>
        </div>
        <div class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p class="text-sm font-medium text-slate-600">Ocupados</p>
          <p class="mt-1 text-3xl font-bold text-amber-700">{{ occupiedBeds }}</p>
        </div>
      </div>
    </div>

    <div class="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div class="flex items-center justify-between border-b border-slate-100 px-4 py-3">
        <h3 class="text-lg font-semibold text-slate-900">Situação dos leitos</h3>
        <span class="text-sm text-slate-500">Sem `PATCH` oficial no YAML para alterar disponibilidade</span>
      </div>
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-100 text-sm">
          <thead class="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-500">
            <tr>
              <th class="px-4 py-3">Leito</th>
              <th class="px-4 py-3">Status legado</th>
              <th class="px-4 py-3">Disponibilidade derivada</th>
              <th class="px-4 py-3">Ocupação</th>
              <th class="px-4 py-3">Paciente atual</th>
              <th class="px-4 py-3">Próximo paciente</th>
              <th class="px-4 py-3">Ação</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="bed in bedsStore.beds" :key="bed.id" class="hover:bg-slate-50">
              <td class="px-4 py-3 font-semibold text-slate-900">{{ bed.code }}</td>
              <td class="px-4 py-3">
                <UiBadge class="border-slate-200 bg-zinc-100 text-zinc-700">
                  {{ bed.legacy_status || 'N/A' }}
                </UiBadge>
              </td>
              <td class="px-4 py-3">
                <UiBadge :class="bed.availability_status === 'DISPONIVEL' ? 'border-teal-200 bg-teal-50 text-teal-700' : 'border-slate-200 bg-slate-100 text-slate-700'">
                  {{ bed.availability_status === 'DISPONIVEL' ? 'Disponível para reserva' : 'Não disponível para reserva' }}
                </UiBadge>
              </td>
              <td class="px-4 py-3">
                <UiBadge :class="bed.occupancy_status === 'LIVRE' ? 'border-sky-200 bg-sky-50 text-sky-700' : 'border-amber-200 bg-amber-50 text-amber-700'">
                  {{ bed.occupancy_status === 'LIVRE' ? 'Livre' : 'Ocupado' }}
                </UiBadge>
              </td>
              <td class="px-4 py-3">
                <span class="text-xs text-slate-600">{{ bed.current_patient_id || 'Nenhum' }}</span>
              </td>
              <td class="px-4 py-3">
                <span class="text-xs text-slate-600">{{ bed.next_patient_id || 'Nenhum' }}</span>
              </td>
              <td class="px-4 py-3">
                <span class="text-xs text-amber-700">
                  Backend precisa expor endpoint oficial para alterar disponibilidade.
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue';
import UiButton from '../components/ui/Button.vue';
import UiBadge from '../components/ui/Badge.vue';
import { useBedsStore } from '../stores/beds';
import { useRoleStore } from '../stores/role';

const bedsStore = useBedsStore();
const roleStore = useRoleStore();

const isIcu = computed(() => roleStore.role === 'ICU');

const reload = async () => {
  if (isIcu.value) {
    await bedsStore.load();
  } else {
    bedsStore.reset();
  }
};

onMounted(async () => {
  await reload();
});

watch(
  () => roleStore.role,
  async () => {
    await reload();
  }
);

const totalBeds = computed(() => bedsStore.beds.length);
const occupiedBeds = computed(() => bedsStore.beds.filter(b => b.occupancy_status === 'OCUPADO').length);
const reservedBeds = computed(() => bedsStore.beds.filter(b => !!b.next_patient_id).length);
</script>
