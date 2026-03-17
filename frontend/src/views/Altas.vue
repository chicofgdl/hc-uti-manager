<template>
  <section class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="space-y-1">
        <h2 class="text-3xl font-bold text-slate-900">Transferências Centro Cirúrgico → UTI</h2>
        <p class="text-sm text-slate-600">Solicite transferência após reserva aceita ou selecione um leito livre.</p>
        <p class="text-sm text-amber-700">{{ profileHint }}</p>
      </div>
      <UiButton variant="outline" size="sm" @click="reload">Atualizar</UiButton>
    </div>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <div class="lg:col-span-1 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <template v-if="isCc">
          <h3 class="text-lg font-semibold text-slate-900 mb-2">Solicitar transferência (Centro Cirúrgico)</h3>
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
              Reserva aceita (opcional)
              <select v-model.number="form.reservationId" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm">
                <option :value="null">Sem vínculo com reserva</option>
                <option v-for="reservation in acceptedReservations" :key="reservation.id" :value="reservation.id">
                  #{{ reservation.id }} · Paciente {{ reservation.patient.external_id }} · Leito {{ reservation.bed_id ? bedCode(reservation.bed_id) : 'N/A' }}
                </option>
              </select>
            </label>
            <label class="block text-sm font-medium text-slate-700">
              Leito (opcional)
              <select v-model.number="form.bedId" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm">
                <option :value="null">Usar leito da reserva ou automático</option>
                <option v-for="bed in bedsStore.availableBeds" :key="bed.id" :value="bed.id">
                  {{ bed.code }}
                </option>
              </select>
            </label>
            <label class="block text-sm font-medium text-slate-700">
              Observação
              <textarea
                v-model="form.notes"
                rows="3"
                class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              />
            </label>
            <UiButton type="submit" class="w-full" :disabled="!form.patientId">Solicitar transferência</UiButton>
          </form>
        </template>
        <div v-else class="rounded-lg border border-amber-200 bg-amber-50 px-3 py-3 text-sm text-amber-800">
          Solicitação de transferência é permitida apenas para a conta de cirurgia.
        </div>
      </div>

      <div class="lg:col-span-2 space-y-6">
        <div class="rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div class="flex items-center justify-between border-b border-slate-100 px-4 py-3">
            <div>
              <h3 class="text-lg font-semibold text-slate-900">Pendentes (UTI decide)</h3>
              <p class="text-xs text-slate-500">Aceitar ocupa o leito e notifica o CC.</p>
            </div>
          </div>
          <div v-if="!isIcu" class="px-4 py-6 text-sm text-slate-500">
            Entre com uma conta UTI para aceitar ou negar transferências.
          </div>
          <div v-else-if="pendingTransfers.length === 0" class="px-4 py-6 text-sm text-slate-500">
            Nenhuma transferência pendente.
          </div>
          <div v-else class="divide-y divide-slate-100">
            <div v-for="tr in pendingTransfers" :key="tr.id" class="px-4 py-4 flex flex-wrap items-center gap-3">
              <div class="flex-1">
                <p class="text-sm font-semibold text-slate-900">Paciente {{ tr.patient.external_id }}</p>
                <p class="text-xs text-slate-500">Reserva: {{ tr.reservation_id ?? 'N/A' }}</p>
              </div>
              <select v-model="selectedBed[tr.id]" class="rounded-lg border border-slate-200 px-2 py-1 text-sm">
                <option :value="null">Leito da reserva/automático</option>
                <option v-for="bed in bedsStore.availableBeds" :key="bed.id" :value="bed.id">
                  {{ bed.code }}
                </option>
              </select>
              <div class="flex gap-2">
                <UiButton size="sm" @click="decide(tr.id, 'ACCEPT')">Aceitar</UiButton>
                <UiButton size="sm" variant="destructive" @click="decide(tr.id, 'DENY')">Negar</UiButton>
              </div>
            </div>
          </div>
        </div>

        <div class="rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div class="flex items-center justify-between border-b border-slate-100 px-4 py-3">
            <h3 class="text-lg font-semibold text-slate-900">Histórico</h3>
          </div>
          <div v-if="transfersStore.transfers.length === 0" class="px-4 py-6 text-sm text-slate-500">
            Nenhuma transferência registrada.
          </div>
          <div v-else class="divide-y divide-slate-100">
            <div v-for="tr in transfersStore.transfers" :key="tr.id" class="px-4 py-4 flex flex-wrap items-center gap-3">
              <div class="flex-1">
                <p class="text-sm font-semibold text-slate-900">Paciente {{ tr.patient.external_id }}</p>
                <p class="text-xs text-slate-500">Status: <UiBadge :class="statusClass(tr.status)">{{ tr.status }}</UiBadge></p>
              </div>
              <span v-if="tr.bed_id" class="text-xs text-slate-600">Leito {{ bedCode(tr.bed_id) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, watch } from 'vue';
import UiButton from '../components/ui/Button.vue';
import UiBadge from '../components/ui/Badge.vue';
import { useTransfersStore } from '../stores/transfers';
import { useBedsStore } from '../stores/beds';
import { useReservationsStore } from '../stores/reservations';
import { useRoleStore } from '../stores/role';
import { useToast } from 'vue-toastification';

const transfersStore = useTransfersStore();
const bedsStore = useBedsStore();
const reservationsStore = useReservationsStore();
const roleStore = useRoleStore();
const toast = useToast();

const form = reactive({
  patientId: '',
  reservationId: null as number | null,
  bedId: null as number | null,
  notes: '',
});

const selectedBed: Record<number, number | null> = reactive({});

onMounted(() => {
  reload();
});

watch(
  () => roleStore.role,
  () => {
    reload();
  }
);

const reload = () => {
  transfersStore.load();
  bedsStore.load();
  reservationsStore.load();
};

const pendingTransfers = computed(() => transfersStore.pending);
const acceptedReservations = computed(() => reservationsStore.accepted);
const isIcu = computed(() => roleStore.role === 'ICU');
const isCc = computed(() => roleStore.role === 'SURGICAL_CENTER');
const profileHint = computed(() => (
  isCc.value
    ? 'Conta de cirurgia ativa: você pode solicitar transferências.'
    : 'Conta UTI ativa: você pode decidir transferências pendentes.'
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
    toast.error('Ação permitida apenas para a conta de cirurgia.');
    return;
  }
  try {
    await transfersStore.create({
      patientId: form.patientId,
      reservationId: form.reservationId || null,
      bedId: form.bedId || null,
      notes: form.notes || undefined,
    });
    form.patientId = '';
    form.reservationId = null;
    form.bedId = null;
    form.notes = '';
  } catch (error: any) {
    toast.error(error.response?.data?.detail || 'Erro ao solicitar transferência.');
  }
};

const decide = async (id: number, decision: 'ACCEPT' | 'DENY') => {
  if (!isIcu.value) {
    toast.error('Ação permitida apenas para a conta UTI.');
    return;
  }
  try {
    await transfersStore.decide(id, decision, selectedBed[id] || null);
  } catch (error: any) {
    toast.error(error.response?.data?.detail || 'Erro ao decidir transferência.');
  }
};

const bedCode = (bedId: number) => {
  const bed = bedsStore.beds.find((item) => item.id === bedId);
  return bed?.code || String(bedId);
};
</script>
