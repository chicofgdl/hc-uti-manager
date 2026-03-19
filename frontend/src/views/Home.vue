<template>
  <section class="space-y-6">
    <div class="space-y-3 mb-4">
      <div class="flex items-center justify-between">
        <h2 class="text-3xl font-bold text-slate-900">{{ isIcu ? 'Leitos da UTI' : 'Leitos liberados para reserva' }}</h2>
        <UiButton size="sm" variant="outline" @click="reload">
          Atualizar
        </UiButton>
      </div>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p class="text-sm font-medium text-slate-600">Total de leitos</p>
          <p class="mt-1 text-3xl font-bold text-slate-900">{{ totalBeds }}</p>
        </div>
        <div class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p class="text-sm font-medium text-slate-600">{{ isIcu ? 'Com alta solicitada e sem próximo paciente' : 'Liberados para reserva' }}</p>
          <p class="mt-1 text-3xl font-bold text-emerald-700">{{ isIcu ? bedsStore.availableCount : bedsStore.reservableCount }}</p>
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
      </div>
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-100 text-sm">
          <thead class="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-500">
            <tr>
              <th class="px-4 py-3">Leito</th>
              <th class="px-4 py-3">Status</th>
              <th class="px-4 py-3">Disponibilidade para reserva</th>
              <th class="px-4 py-3">Ocupação</th>
              <th class="px-4 py-3">Paciente atual</th>
              <th class="px-4 py-3">Próximo paciente</th>
              <th class="px-4 py-3">Ação</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="bed in visibleBeds" :key="bed.id" class="hover:bg-slate-50">
              <td class="px-4 py-3 font-semibold text-slate-900">{{ bed.code }}</td>
              <td class="px-4 py-3">
                <UiBadge class="border-slate-200 bg-zinc-100 text-zinc-700">
                  {{ bed.legacy_status || 'N/A' }}
                </UiBadge>
              </td>
              <td class="px-4 py-3">
                <UiBadge :class="bed.availability_status === 'DISPONIVEL' ? 'border-teal-200 bg-teal-50 text-teal-700' : 'border-slate-200 bg-slate-100 text-slate-700'">
                  {{ bed.availability_status === 'DISPONIVEL' ? 'Liberado para reserva' : 'Bloqueado para reserva' }}
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
                <div v-if="isIcu" class="flex flex-col items-start gap-2">
                  <UiButton
                    size="sm"
                    :variant="bed.availability_status === 'DISPONIVEL' ? 'destructive' : 'default'"
                    @click="toggleReservationAvailability(bed.id, bed.availability_status !== 'DISPONIVEL')"
                  >
                    {{ bed.availability_status === 'DISPONIVEL' ? 'Bloquear reserva' : 'Liberar para reserva' }}
                  </UiButton>
                </div>
                <span v-else class="text-xs text-slate-500">-</span>
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
import { useToast } from 'vue-toastification';

const bedsStore = useBedsStore();
const roleStore = useRoleStore();
const toast = useToast();

const isIcu = computed(() => roleStore.role === 'ICU');
const visibleBeds = computed(() => (isIcu.value ? bedsStore.beds : bedsStore.reservableBeds));

const reload = async () => {
  if (isIcu.value) {
    await bedsStore.load();
  } else {
    await bedsStore.loadReservable();
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

const totalBeds = computed(() => visibleBeds.value.length);
const occupiedBeds = computed(() => visibleBeds.value.filter(b => b.occupancy_status === 'OCUPADO').length);
const reservedBeds = computed(() => visibleBeds.value.filter(b => !!b.next_patient_id).length);

const toggleReservationAvailability = async (bedId: string, shouldBeAvailable: boolean) => {
  try {
    await bedsStore.toggleAvailability(bedId, shouldBeAvailable);
  } catch (error: any) {
    toast.error(error.response?.data?.detail || error.message || 'Erro ao alterar disponibilidade do leito.');
  }
};
</script>
