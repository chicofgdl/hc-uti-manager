<template>
  <section class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="space-y-1">
        <h2 class="text-3xl font-bold text-slate-900">Reservas de Leito</h2>
        <p class="text-sm text-slate-600">
          Esta tela usa as rotas legadas do YAML para busca de paciente, disponibilidade de leitos e solicitação de reserva.
        </p>
        <p class="text-sm text-amber-700">{{ profileHint }}</p>
        <p v-if="isCc" class="text-xs text-slate-500">
          O YAML não expõe listagem de solicitações do Centro Cirúrgico. As solicitações criadas nesta sessão aparecem localmente abaixo, agora com o `id` real devolvido pelo backend.
        </p>
      </div>
      <UiButton variant="outline" size="sm" @click="reload">Atualizar</UiButton>
    </div>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm lg:col-span-1">
        <template v-if="isCc">
          <h3 class="mb-2 text-lg font-semibold text-slate-900">Criar solicitação</h3>
          <form class="space-y-3" @submit.prevent="handleCreate">
            <label class="block text-sm font-medium text-slate-700">
              Buscar paciente
              <input
                v-model="form.patientQuery"
                type="text"
                placeholder="Digite código, nome ou outro dado disponível"
                class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              />
            </label>
            <div class="max-h-56 overflow-auto rounded-lg border border-slate-200">
              <button
                v-for="patient in filteredPatients"
                :key="patient.id"
                type="button"
                class="flex w-full flex-col items-start gap-1 border-b border-slate-100 px-3 py-2 text-left text-sm last:border-b-0 hover:bg-slate-50"
                :class="selectedPatient?.id === patient.id ? 'bg-blue-50' : ''"
                @click="selectPatient(patient)"
              >
                <span class="font-semibold text-slate-900">{{ patient.label }}</span>
                <span class="text-xs text-slate-500">
                  Prontuário {{ patient.id }} | Especialidade {{ patient.specialty }} | Idade {{ patient.age }}
                  <span v-if="patient.ageEstimated"> (estimada)</span>
                </span>
              </button>
              <div v-if="loadingPatients" class="px-3 py-4 text-sm text-slate-500">
                Carregando pacientes...
              </div>
              <div v-else-if="filteredPatients.length === 0" class="px-3 py-4 text-sm text-slate-500">
                Nenhum paciente encontrado para o filtro informado.
              </div>
            </div>
            <p v-if="selectedPatient" class="rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
              Prontuário {{ selectedPatient.id }} | Especialidade {{ selectedPatient.specialty }} | Idade enviada {{ selectedPatient.age }}
              <span v-if="selectedPatient.ageEstimated"> (estimada)</span>
              <span v-if="selectedPatient.specialtyMocked"> | Especialidade preenchida como "Não informado"</span>
            </p>
            <p v-else class="text-xs text-slate-500">
              Digite para filtrar a lista e clique em um paciente para selecioná-lo.
            </p>
            <UiButton type="submit" class="w-full" :disabled="!selectedPatient">
              Enviar solicitação
            </UiButton>
          </form>
        </template>
        <div v-else class="rounded-lg border border-amber-200 bg-amber-50 px-3 py-3 text-sm text-amber-800">
          Somente a conta de cirurgia cria solicitações de reserva.
        </div>
      </div>

      <div class="space-y-6 lg:col-span-2">
        <div v-if="isCc" class="rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div class="border-b border-slate-100 px-4 py-3">
            <h3 class="text-lg font-semibold text-slate-900">Leitos disponíveis para reserva</h3>
          </div>
          <div class="grid grid-cols-1 gap-4 border-b border-slate-100 px-4 py-4 md:grid-cols-2">
            <div class="rounded-lg border border-slate-200 bg-slate-50 p-4">
              <p class="text-sm font-medium text-slate-600">Quantidade via `/leitos/quantidade-disponiveis`</p>
              <p class="mt-1 text-3xl font-bold text-emerald-700">{{ bedsStore.reservableCount }}</p>
            </div>
          </div>
          <div v-if="bedsStore.reservableBeds.length === 0" class="px-4 py-6 text-sm text-slate-500">
            Nenhum leito disponível para reserva no momento.
          </div>
          <div v-else class="divide-y divide-slate-100">
            <div v-for="bed in bedsStore.reservableBeds" :key="bed.id" class="flex flex-wrap items-center gap-3 px-4 py-4">
              <div class="min-w-0 flex-1">
                <p class="text-sm font-semibold text-slate-900">Leito {{ bed.code }}</p>
                <p class="text-xs text-slate-500">
                  Ocupação atual: {{ bed.occupancy_status === 'OCUPADO' ? 'Ocupado' : 'Livre' }}
                  <span v-if="bed.current_patient_id" class="ml-2">Paciente atual {{ bed.current_patient_id }}</span>
                </p>
              </div>
              <UiBadge class="border-teal-200 bg-teal-50 text-teal-700">Disponível para reserva</UiBadge>
            </div>
          </div>
        </div>

        <div class="rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div class="border-b border-slate-100 px-4 py-3">
            <h3 class="text-lg font-semibold text-slate-900">Pendentes para decisão da UTI</h3>
          </div>
          <div v-if="!isIcu" class="px-4 py-6 text-sm text-slate-500">
            Entre com uma conta UTI para aprovar ou negar solicitações.
          </div>
          <div v-else-if="pendingReservations.length === 0" class="px-4 py-6 text-sm text-slate-500">
            Nenhuma solicitação pendente.
          </div>
          <div v-else class="divide-y divide-slate-100">
            <div v-for="res in pendingReservations" :key="res.id" class="flex flex-wrap items-center gap-3 px-4 py-4">
              <div class="min-w-0 flex-1">
                <p class="text-sm font-semibold text-slate-900">
                  Paciente {{ res.patient.external_id }}{{ res.especialidade_paciente ? ` - ${res.especialidade_paciente}` : '' }}
                </p>
                <p class="text-xs text-slate-500">
                  Idade {{ res.idade_paciente ?? 'N/A' }} | Criado em {{ formatDate(res.created_at) }}
                </p>
              </div>
              <select
                v-model="selectedBed[res.id]"
                class="rounded-lg border border-slate-200 px-2 py-1 text-sm"
              >
                <option :value="null">Selecione um leito</option>
                <option v-for="bed in bedsStore.availableBeds" :key="bed.id" :value="bed.code">
                  {{ bed.code }}
                </option>
              </select>
              <div class="flex gap-2">
                <UiButton size="sm" @click="decide(res.id, 'ACCEPT')">Aprovar</UiButton>
                <UiButton size="sm" variant="destructive" @click="decide(res.id, 'DENY')">Negar</UiButton>
              </div>
            </div>
          </div>
        </div>

        <div class="rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div class="flex items-center justify-between border-b border-slate-100 px-4 py-3">
            <h3 class="text-lg font-semibold text-slate-900">
              {{ isCc ? 'Solicitações criadas nesta sessão' : 'Solicitações conhecidas pela UTI' }}
            </h3>
          </div>
          <div v-if="visibleReservations.length === 0" class="px-4 py-6 text-sm text-slate-500">
            Nenhuma solicitação para exibir.
          </div>
          <div v-else class="divide-y divide-slate-100">
            <div v-for="res in visibleReservations" :key="res.id" class="flex flex-wrap items-center gap-3 px-4 py-4">
              <div class="min-w-0 flex-1">
                <p class="text-sm font-semibold text-slate-900">
                  Paciente {{ res.patient.external_id }}{{ res.especialidade_paciente ? ` - ${res.especialidade_paciente}` : '' }}
                </p>
                <p class="text-xs text-slate-500">
                  Status:
                  <UiBadge :class="statusClass(res.status)">{{ res.status }}</UiBadge>
                  <span v-if="res.lto_lto_id || res.bed_code" class="ml-2 text-slate-600">Leito {{ res.lto_lto_id || res.bed_code }}</span>
                  <span v-if="res.source === 'mock-local'" class="ml-2 text-amber-700">Registro local da sessão</span>
                </p>
              </div>
              <UiButton
                v-if="['PENDENTE', 'ACEITA'].includes(res.status)"
                size="sm"
                variant="outline"
                @click="cancel(res.id)"
              >
                Cancelar
              </UiButton>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue';
import UiBadge from '../components/ui/Badge.vue';
import UiButton from '../components/ui/Button.vue';
import { useBedsStore } from '../stores/beds';
import { useReservationsStore } from '../stores/reservations';
import { useRoleStore } from '../stores/role';
import { useToast } from 'vue-toastification';
import api from '../services/api';

type PatientOption = {
  id: string;
  label: string;
  searchText: string;
  specialty: string;
  specialtyMocked: boolean;
  age: number;
  ageEstimated: boolean;
};

const bedsStore = useBedsStore();
const reservationsStore = useReservationsStore();
const roleStore = useRoleStore();
const toast = useToast();

const form = reactive({
  patientQuery: '',
});

const selectedPatient = ref<PatientOption | null>(null);
const patientOptions = ref<PatientOption[]>([]);
const loadingPatients = ref(false);
const selectedBed: Record<number, string | null> = reactive({});

const patientIdCandidates = ['Prontuário', 'Prontuario', 'PRONTUARIO', 'codigo', 'Código', 'external_id'] as const;
const patientNameCandidates = ['Nome', 'nome', 'NM_PESSOA_FISICA', 'paciente', 'name'] as const;
const specialtyCandidates = ['Especialidade', 'especialidade', 'specialty'] as const;
const birthDateCandidates = ['Data Nasc.', 'dt_nascimento', 'data_nascimento'] as const;

const normalizeValue = (raw: unknown): string => {
  if (raw === null || raw === undefined) return '';
  return String(raw).trim();
};

const findValue = (row: Record<string, unknown>, keys: readonly string[]): string => {
  for (const key of keys) {
    const value = normalizeValue(row[key]);
    if (value) return value;
  }
  return '';
};

const buildSearchText = (row: Record<string, unknown>) =>
  Object.values(row)
    .map((value) => normalizeValue(value).toLowerCase())
    .filter(Boolean)
    .join(' ');

const parseAge = (birthDate: string): number | null => {
  if (!birthDate) return null;
  const parts = birthDate.includes('/') ? birthDate.split('/') : birthDate.split('-');
  if (parts.length !== 3) return null;
  let day = 1;
  let month = 1;
  let year = 1900;
  if (birthDate.includes('/')) {
    day = Number(parts[0]);
    month = Number(parts[1]);
    year = Number(parts[2]);
  } else {
    year = Number(parts[0]);
    month = Number(parts[1]);
    day = Number(parts[2]);
  }
  if (!year || !month || !day) return null;
  const today = new Date();
  let age = today.getFullYear() - year;
  const monthDiff = today.getMonth() + 1 - month;
  const dayDiff = today.getDate() - day;
  if (monthDiff < 0 || (monthDiff === 0 && dayDiff < 0)) {
    age -= 1;
  }
  return age >= 0 ? age : null;
};

const loadPatientOptions = async () => {
  loadingPatients.value = true;
  try {
    const { data } = await api.get('/api/pacientes');
    const rows: Array<Record<string, unknown>> = Array.isArray(data) ? data : [];
    patientOptions.value = rows
      .map((row) => {
        const id = findValue(row, patientIdCandidates);
        if (!id) return null;
        const name = findValue(row, patientNameCandidates);
        const specialtyRaw = findValue(row, specialtyCandidates);
        const specialty = specialtyRaw || 'Nao informado';
        const birthDate = findValue(row, birthDateCandidates);
        const age = parseAge(birthDate);
        return {
          id,
          label: name ? `${id} - ${name}` : id,
          searchText: buildSearchText(row),
          specialty,
          specialtyMocked: !specialtyRaw,
          age: age ?? 0,
          ageEstimated: age === null,
        };
      })
      .filter((option): option is PatientOption => option !== null);
  } catch {
    patientOptions.value = [];
    toast.error('Não foi possível carregar pacientes.');
  } finally {
    loadingPatients.value = false;
  }
};

const filteredPatients = computed(() => {
  const query = form.patientQuery.trim().toLowerCase();
  if (!query) return patientOptions.value;
  return patientOptions.value.filter((patient) => patient.searchText.includes(query));
});

const selectPatient = (patient: PatientOption) => {
  selectedPatient.value = patient;
};

const isIcu = computed(() => roleStore.role === 'ICU');
const isCc = computed(() => roleStore.role === 'SURGICAL_CENTER');
const pendingReservations = computed(() => reservationsStore.pending);
const visibleReservations = computed(() => reservationsStore.visibleReservations);
const profileHint = computed(() => (
  isCc.value
    ? 'Conta de cirurgia: consulta disponibilidade, cria e cancela solicitações.'
    : 'Conta UTI: pode listar, aprovar, negar e cancelar solicitações.'
));

const reload = async () => {
  if (isIcu.value) {
    await Promise.all([reservationsStore.load(), bedsStore.load()]);
  } else if (isCc.value) {
    await Promise.all([reservationsStore.load(), bedsStore.loadReservable()]);
  } else {
    await reservationsStore.load();
    bedsStore.reset();
  }
};

onMounted(async () => {
  await Promise.all([reload(), loadPatientOptions()]);
});

watch(
  () => roleStore.role,
  async () => {
    await reload();
    if (isCc.value && patientOptions.value.length === 0) {
      await loadPatientOptions();
    }
  }
);

const statusClass = (status: string) => {
  switch (status) {
    case 'PENDENTE':
      return 'border-amber-200 bg-amber-50 text-amber-800';
    case 'ACEITA':
      return 'border-teal-200 bg-teal-50 text-teal-700';
    case 'NEGADA':
      return 'border-rose-200 bg-rose-50 text-rose-700';
    case 'CANCELADA':
      return 'border-slate-200 bg-slate-100 text-slate-700';
    default:
      return 'border-zinc-200 bg-zinc-100 text-zinc-700';
  }
};

const handleCreate = async () => {
  if (!selectedPatient.value) {
    toast.error('Selecione um paciente.');
    return;
  }
  if (selectedPatient.value.ageEstimated) {
    toast.info('A idade não veio explicitamente da API e foi estimada a partir da data de nascimento. Se isso não for válido, alinhe o contrato com o backend.');
  }
  if (selectedPatient.value.specialtyMocked) {
    toast.info('A especialidade não veio da API e foi preenchida como "Nao informado".');
  }
  try {
    await reservationsStore.create({
      prontuario: selectedPatient.value.id,
      idade: selectedPatient.value.age,
      especialidade: selectedPatient.value.specialty,
    });
    form.patientQuery = '';
    selectedPatient.value = null;
  } catch (error: any) {
    toast.error(error.response?.data?.detail || error.message || 'Erro ao criar solicitação.');
  }
};

const decide = async (id: number, decision: 'ACCEPT' | 'DENY') => {
  try {
    await reservationsStore.decide(id, decision, selectedBed[id] || null);
  } catch (error: any) {
    toast.error(error.response?.data?.detail || error.message || 'Erro ao decidir solicitação.');
  }
};

const cancel = async (id: number) => {
  try {
    if (isCc.value) {
      await reservationsStore.cancelByCc(id);
    } else {
      await reservationsStore.cancelByIcu(id);
    }
  } catch (error: any) {
    toast.error(error.response?.data?.detail || error.message || 'Erro ao cancelar solicitação.');
  }
};

const formatDate = (value: string) => new Date(value).toLocaleString('pt-BR', { hour12: false });
</script>
