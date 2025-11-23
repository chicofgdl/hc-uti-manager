<template>
  <section class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="text-3xl font-bold text-slate-900">Visao Geral dos Leitos</h2>
      </div>
      <UiButton variant="outline" size="sm" class="shadow-sm">
        <FunnelIcon class="h-5 w-5 text-slate-500" />
        Filtrar
      </UiButton>
    </div>

    <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      <BedCard
        v-for="leito in mockLeitos"
        :key="leito.leitoNumero"
        v-bind="leito"
      />
    </div>
  </section>
</template>

<script setup lang="ts">
import { FunnelIcon } from '@heroicons/vue/24/outline';
import BedCard from '../components/BedCard.vue';
import UiButton from '../components/ui/Button.vue';

type BedStatus = 'disponivel' | 'ocupado' | 'higienizacao' | 'desativado' | 'alta';
type BedType = 'cirurgico' | 'hem' | 'obstetrico' | 'outro' | 'nao_definido';

type Patient = {
  prontuario: string;
  idade: number;
  especialidade: string;
};

type Leito = {
  leitoNumero: string;
  status: BedStatus;
  tipo: BedType;
  pacienteAtual?: Patient;
  proximoPaciente?: Patient;
  tipoReserva?: string;
  sinalizacaoTransferencia?: boolean;
};

const mockLeitos: Leito[] = [
  {
    leitoNumero: '01',
    status: 'ocupado',
    tipo: 'cirurgico',
    pacienteAtual: {
      prontuario: '123456',
      idade: 67,
      especialidade: 'Cardiologia',
    },
    proximoPaciente: {
      prontuario: '654321',
      idade: 54,
      especialidade: 'Neurologia',
    },
    tipoReserva: 'Cirurgico',
  },
  {
    leitoNumero: '02',
    status: 'disponivel',
    tipo: 'cirurgico',
  },
  {
    leitoNumero: '03',
    status: 'alta',
    tipo: 'hem',
    pacienteAtual: {
      prontuario: '456789',
      idade: 45,
    especialidade: 'Oncologia',
    },
    sinalizacaoTransferencia: true,
  },
  {
    leitoNumero: '04',
    status: 'higienizacao',
    tipo: 'cirurgico',
  },
  {
    leitoNumero: '05',
    status: 'ocupado',
    tipo: 'hem',
    pacienteAtual: {
      prontuario: '789012',
      idade: 52,
      especialidade: 'Hematologia',
    },
  },
  {
    leitoNumero: '06',
    status: 'desativado',
    tipo: 'nao_definido',
  },
  {
    leitoNumero: '07',
    status: 'ocupado',
    tipo: 'obstetrico',
    pacienteAtual: {
      prontuario: '234567',
      idade: 29,
      especialidade: 'Obstetricia',
    },
  },
  {
    leitoNumero: '08',
    status: 'disponivel',
    tipo: 'outro',
    proximoPaciente: {
      prontuario: '345678',
      idade: 61,
      especialidade: 'Pneumologia',
    },
    tipoReserva: 'Emergencia',
  },
];
</script>
