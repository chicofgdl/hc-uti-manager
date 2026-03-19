<template>
  <div class="space-y-6">
    <div>
      <h1 class="mb-2 text-2xl font-bold">Pacientes</h1>
    </div>

    <Card>
      <div class="flex items-end gap-3">
        <div class="flex-1">
          <label for="pacienteCodigoInput" class="form-label">Buscar paciente por código</label>
          <input
            id="pacienteCodigoInput"
            v-model="pacienteCodigoInput"
            type="number"
            placeholder="Digite o prontuário"
            class="form-control"
          >
        </div>
        <Button @click="fetchPacientePorCodigo" :disabled="loadingPaciente" variant="success">
          <span v-if="loadingPaciente">Buscando...</span>
          <span v-else>Buscar</span>
        </Button>
      </div>
    </Card>

    <Card v-if="pacienteDetalhe">
      <template #header>
        <h2 class="text-lg font-semibold">Detalhes do paciente</h2>
      </template>
      <div class="grid grid-cols-1 gap-4 text-sm md:grid-cols-2">
        <div><span class="font-medium">Prontuário:</span> {{ detailField('Prontuário', 'codigo') }}</div>
        <div><span class="font-medium">Especialidade:</span> {{ detailField('Especialidade', 'especialidade') }}</div>
        <div><span class="font-medium">Data de nascimento:</span> {{ detailField('Data Nasc.', 'dt_nascimento') }}</div>
      </div>
    </Card>

    <Card>
      <DataTable :headers="headers" :items="pacientes" />
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useToast } from 'vue-toastification';
import api from '../services/api';
import Card from '../components/Card.vue';
import DataTable from '../components/DataTable.vue';
import Button from '../components/Button.vue';

const toast = useToast();

const pacienteCodigoInput = ref<number | null>(null);
const loadingPaciente = ref(false);
const pacienteDetalhe = ref<Record<string, unknown> | null>(null);

const headers = ref([
  { text: 'Prontuário', value: 'Prontuário' },
  { text: 'Especialidade', value: 'Especialidade' },
  { text: 'Data de Nascimento', value: 'Data Nasc.' },
]);

const pacientes = ref<Array<Record<string, unknown>>>([]);

const loadPacientes = async () => {
  try {
    const { data } = await api.get('/api/pacientes');
    pacientes.value = Array.isArray(data) ? data : [];
  } catch {
    toast.error('Falha ao carregar a lista de pacientes.');
  }
};

onMounted(async () => {
  await loadPacientes();
});

const fetchPacientePorCodigo = async () => {
  if (!pacienteCodigoInput.value) {
    toast.error('Digite um código.');
    return;
  }
  loadingPaciente.value = true;
  pacienteDetalhe.value = null;
  try {
    const { data } = await api.get(`/api/pacientes/${pacienteCodigoInput.value}`);
    pacienteDetalhe.value = data;
    toast.success('Paciente encontrado.');
  } catch {
    toast.error('Paciente não encontrado.');
  } finally {
    loadingPaciente.value = false;
  }
};

const detailField = (...keys: string[]) => {
  if (!pacienteDetalhe.value) return 'N/A';
  for (const key of keys) {
    const value = pacienteDetalhe.value[key];
    if (value !== null && value !== undefined && String(value).trim() !== '') {
      return value;
    }
  }
  return 'N/A';
};
</script>
