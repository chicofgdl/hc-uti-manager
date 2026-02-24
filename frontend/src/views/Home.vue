<template>
  <section class="space-y-6">
    <div class="space-y-3 mb-4">
      <div class="flex items-center justify-between">
        <h2 class="text-3xl font-bold text-slate-900">Leitos da UTI</h2>
        <UiButton size="sm" variant="outline" @click="bedsStore.load">
          Atualizar
        </UiButton>
      </div>
      <p v-if="!isIcu" class="text-sm text-amber-700">
        Perfil ativo: CC. Visualização em modo leitura; para disponibilizar/bloquear leitos, troque para UTI.
      </p>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p class="text-sm font-medium text-slate-600">Total de leitos</p>
          <p class="mt-1 text-3xl font-bold text-slate-900">{{ totalBeds }}</p>
        </div>
        <div class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p class="text-sm font-medium text-slate-600">Disponíveis para reserva</p>
          <p class="mt-1 text-3xl font-bold text-emerald-700">{{ bedsStore.availableCount }}</p>
        </div>
        <div class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p class="text-sm font-medium text-slate-600">Reservados (aguardando paciente)</p>
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
        <h3 class="text-lg font-semibold text-slate-900">Controle de disponibilidade</h3>
        <span class="text-sm text-slate-500">Clique para liberar ou bloquear para reserva</span>
      </div>
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-100 text-sm">
          <thead class="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-500">
            <tr>
              <th class="px-4 py-3">Leito</th>
              <th class="px-4 py-3">Disponibilidade</th>
              <th class="px-4 py-3">Ocupação</th>
              <th class="px-4 py-3">Ações</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="bed in bedsStore.beds" :key="bed.id" class="hover:bg-slate-50">
              <td class="px-4 py-3 font-semibold text-slate-900">{{ bed.code }}</td>
              <td class="px-4 py-3">
                <UiBadge :class="bed.availability_status === 'DISPONIVEL' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-100 text-slate-700 border-slate-200'">
                  {{ bed.availability_status === 'DISPONIVEL' ? 'Disponível' : 'Não disponível' }}
                </UiBadge>
              </td>
              <td class="px-4 py-3">
                <UiBadge :class="bed.occupancy_status === 'LIVRE' ? 'bg-blue-50 text-blue-700 border-blue-200' : 'bg-amber-50 text-amber-700 border-amber-200'">
                  {{ bed.occupancy_status === 'LIVRE' ? 'Livre' : 'Ocupado' }}
                </UiBadge>
              </td>
              <td class="px-4 py-3">
                <div class="flex gap-2">
                  <UiButton
                    v-if="isIcu"
                    size="xs"
                    variant="outline"
                    :disabled="bed.occupancy_status !== 'LIVRE' && bed.availability_status === 'DISPONIVEL'"
                    @click="handleToggleAvailability(bed.id, bed.availability_status !== 'DISPONIVEL')"
                  >
                    {{ bed.availability_status === 'DISPONIVEL' ? 'Bloquear reserva' : 'Liberar reserva' }}
                  </UiButton>
                  <span v-else class="text-xs text-slate-500">Somente UTI</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import UiButton from '../components/ui/Button.vue';
import UiBadge from '../components/ui/Badge.vue';
import { useBedsStore } from '../stores/beds';
import { useRoleStore } from '../stores/role';
import { useToast } from 'vue-toastification';

const bedsStore = useBedsStore();
const roleStore = useRoleStore();
const toast = useToast();

onMounted(() => {
  bedsStore.load();
});

const isIcu = computed(() => roleStore.role === 'ICU');
const totalBeds = computed(() => bedsStore.beds.length);
const occupiedBeds = computed(() => bedsStore.beds.filter(b => b.occupancy_status === 'OCUPADO').length);
const reservedBeds = computed(() =>
  bedsStore.beds.filter(b => b.occupancy_status === 'LIVRE' && b.availability_status === 'NAO_DISPONIVEL').length
);

const handleToggleAvailability = async (bedId: number, nextAvailability: boolean) => {
  if (!isIcu.value) {
    toast.error('Ação permitida apenas para o perfil UTI.');
    return;
  }
  await bedsStore.toggleAvailability(bedId, nextAvailability);
};
</script>
