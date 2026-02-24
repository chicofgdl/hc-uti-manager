<template>
  <section class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="space-y-1">
        <h2 class="text-3xl font-bold text-slate-900">Reservas de Leito</h2>
        <p class="text-sm text-slate-600">
          CC solicita, UTI decide. Use o seletor de perfil no topo para ver notificações do papel correspondente.
        </p>
        <p class="text-sm text-amber-700">{{ profileHint }}</p>
      </div>
      <div class="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
        <p class="text-sm text-slate-600">Leitos disponíveis</p>
        <span class="text-2xl font-bold text-emerald-700">{{ bedsStore.availableCount }}</span>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <div class="lg:col-span-1 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <template v-if="isCc">
          <h3 class="text-lg font-semibold text-slate-900 mb-2">Solicitar reserva (CC)</h3>
          <form class="space-y-3" @submit.prevent="handleCreate">
            <label class="block text-sm font-medium text-slate-700">
              Prontuário do paciente
              <input
                v-model="form.patientId"
                required
                class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                placeholder="Ex: 77001"
              />
            </label>
            <label class="block text-sm font-medium text-slate-700">
              Observação
              <textarea
                v-model="form.notes"
                class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                rows="3"
                placeholder="Motivo clínico, horário previsto..."
              />
            </label>
            <UiButton type="submit" class="w-full" :disabled="!form.patientId">
              Enviar solicitação
            </UiButton>
          </form>
        </template>
        <div v-else class="rounded-lg border border-amber-200 bg-amber-50 px-3 py-3 text-sm text-amber-800">
          Solicitação de reserva é permitida apenas para o perfil CC.
        </div>
      </div>

      <div class="lg:col-span-2 space-y-6">
        <div class="rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div class="flex items-center justify-between border-b border-slate-100 px-4 py-3">
            <div>
              <h3 class="text-lg font-semibold text-slate-900">Pendentes (UTI decide)</h3>
              <p class="text-xs text-slate-500">Aceitar define leito; negar informa CC.</p>
            </div>
          </div>
          <div v-if="!isIcu" class="px-4 py-6 text-sm text-slate-500">
            Troque para o perfil UTI para aceitar ou negar solicitações.
          </div>
          <div v-else-if="pendingReservations.length === 0" class="px-4 py-6 text-sm text-slate-500">
            Nenhuma solicitação pendente.
          </div>
          <div v-else class="divide-y divide-slate-100">
            <div v-for="res in pendingReservations" :key="res.id" class="px-4 py-4 flex flex-wrap items-center gap-3">
              <div class="flex-1">
                <p class="text-sm font-semibold text-slate-900">
                  Paciente {{ res.patient.external_id }}
                </p>
                <p class="text-xs text-slate-500">
                  Criado em {{ formatDate(res.created_at) }}
                </p>
              </div>
              <select
                v-model="selectedBed[res.id]"
                class="rounded-lg border border-slate-200 px-2 py-1 text-sm"
              >
                <option :value="null">Alocação automática</option>
                <option v-for="bed in bedsStore.availableBeds" :key="bed.id" :value="bed.id">
                  {{ bed.code }}
                </option>
              </select>
              <div class="flex gap-2">
                <UiButton size="sm" @click="decide(res.id, 'ACCEPT')">Aceitar</UiButton>
                <UiButton size="sm" variant="destructive" @click="decide(res.id, 'DENY')">Negar</UiButton>
              </div>
            </div>
          </div>
        </div>

        <div class="rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div class="flex items-center justify-between border-b border-slate-100 px-4 py-3">
            <h3 class="text-lg font-semibold text-slate-900">{{ isCc ? 'Minhas reservas (CC)' : 'Reservas (UTI)' }}</h3>
            <span class="text-xs text-slate-500">
              {{ isCc ? 'Cancelar envia aviso para UTI.' : 'Cancelar envia aviso para CC.' }}
            </span>
          </div>
          <div v-if="allReservations.length === 0" class="px-4 py-6 text-sm text-slate-500">
            Nenhuma reserva criada.
          </div>
          <div v-else class="divide-y divide-slate-100">
            <div v-for="res in allReservations" :key="res.id" class="px-4 py-4 flex flex-wrap items-center gap-3">
              <div class="flex-1">
                <p class="text-sm font-semibold text-slate-900">Paciente {{ res.patient.external_id }}</p>
                <p class="text-xs text-slate-500">
                  Status:
                  <UiBadge :class="statusClass(res.status)">{{ res.status }}</UiBadge>
                  <span v-if="res.bed_id" class="ml-2 text-slate-600 text-xs">Leito {{ bedCode(res.bed_id) }}</span>
                </p>
              </div>
              <UiButton
                v-if="['PENDENTE', 'ACEITA'].includes(res.status)"
                size="sm"
                variant="outline"
                @click="cancel(res.id)"
              >
                {{ isCc ? 'Cancelar (CC)' : 'Cancelar (UTI)' }}
              </UiButton>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue';
import UiBadge from '../components/ui/Badge.vue';
import UiButton from '../components/ui/Button.vue';
import { useBedsStore } from '../stores/beds';
import { useReservationsStore } from '../stores/reservations';
import { useRoleStore } from '../stores/role';
import { useToast } from 'vue-toastification';

const bedsStore = useBedsStore();
const reservationsStore = useReservationsStore();
const roleStore = useRoleStore();
const toast = useToast();

const form = reactive({
  patientId: '',
  notes: '',
});

const selectedBed: Record<number, number | null> = reactive({});

onMounted(() => {
  bedsStore.load();
  reservationsStore.load();
});

const pendingReservations = computed(() => reservationsStore.pending);
const allReservations = computed(() => reservationsStore.reservations);
const isIcu = computed(() => roleStore.role === 'ICU');
const isCc = computed(() => roleStore.role === 'SURGICAL_CENTER');
const profileHint = computed(() => (
  isCc.value
    ? 'Perfil CC ativo: você pode solicitar e cancelar suas reservas.'
    : 'Perfil UTI ativo: você pode aceitar, negar e cancelar reservas ativas.'
));

const statusClass = (status: string) => {
  switch (status) {
    case 'PENDENTE':
      return 'bg-amber-50 text-amber-700 border-amber-200';
    case 'ACEITA':
      return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    case 'NEGADA':
      return 'bg-rose-50 text-rose-700 border-rose-200';
    default:
      return 'bg-slate-100 text-slate-700 border-slate-200';
  }
};

const handleCreate = async () => {
  if (!isCc.value) {
    toast.error('Ação permitida apenas para o perfil CC.');
    return;
  }
  try {
    await reservationsStore.create({
      patientId: form.patientId,
      notes: form.notes || undefined,
    });
    form.patientId = '';
    form.notes = '';
  } catch (error: any) {
    toast.error(error.response?.data?.detail || 'Erro ao criar reserva.');
  }
};

const decide = async (id: number, decision: 'ACCEPT' | 'DENY') => {
  if (!isIcu.value) {
    toast.error('Ação permitida apenas para o perfil UTI.');
    return;
  }
  try {
    await reservationsStore.decide(id, decision, selectedBed[id] || null);
    bedsStore.load();
  } catch (error: any) {
    toast.error(error.response?.data?.detail || 'Erro ao decidir reserva.');
  }
};

const cancel = async (id: number) => {
  try {
    if (isCc.value) {
      await reservationsStore.cancelByCc(id);
    } else if (isIcu.value) {
      await reservationsStore.cancelByIcu(id);
    } else {
      toast.error('Perfil inválido para cancelar reserva.');
      return;
    }
    bedsStore.load();
  } catch (error: any) {
    toast.error(error.response?.data?.detail || 'Erro ao cancelar.');
  }
};

const formatDate = (value: string) => new Date(value).toLocaleString('pt-BR', { hour12: false });

const bedCode = (bedId: number) => {
  const bed = bedsStore.beds.find((item) => item.id === bedId);
  return bed?.code || String(bedId);
};
</script>
