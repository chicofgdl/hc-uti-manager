<template>
  <section class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h2 class="text-3xl font-bold text-slate-900">Alertas do Sistema</h2>
      <div class="flex flex-wrap gap-2">
        <UiButton variant="outline" size="sm">
          Criticos
        </UiButton>
        <UiButton variant="outline" size="sm">
          Avisos
        </UiButton>
        <UiButton variant="outline" size="sm">
          Informacoes
        </UiButton>
      </div>
    </div>

    <div class="space-y-3">
      <article
        v-for="alerta in alertas"
        :key="alerta.id"
        class="rounded-xl border bg-white shadow-sm"
        :class="alertConfig[alerta.tipo].cardClass"
      >
        <div class="p-4">
          <div class="flex items-start gap-4">
            <div class="rounded-full p-2" :class="alertConfig[alerta.tipo].iconBg">
              <component
                :is="alertConfig[alerta.tipo].icon"
                class="h-5 w-5"
                :class="alertConfig[alerta.tipo].iconColor"
              />
            </div>
            <div class="flex-1 space-y-2">
              <div class="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 class="font-semibold text-slate-900">{{ alerta.titulo }}</h3>
                  <p class="mt-1 text-sm text-slate-600">{{ alerta.mensagem }}</p>
                </div>
                <UiBadge :class="alertConfig[alerta.tipo].badgeClass">
                  {{ formatTipo(alerta.tipo) }}
                </UiBadge>
              </div>
              <div class="flex items-center gap-2 text-xs text-slate-500">
                <ClockIcon class="h-3 w-3" />
                <span>{{ alerta.dataHora }}</span>
              </div>
            </div>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import {
  ExclamationTriangleIcon,
  ExclamationCircleIcon,
  InformationCircleIcon,
  ClockIcon,
} from '@heroicons/vue/24/outline';
import UiBadge from '../components/ui/Badge.vue';
import UiButton from '../components/ui/Button.vue';

type AlertType = 'critico' | 'aviso' | 'info';

type Alert = {
  id: string;
  tipo: AlertType;
  titulo: string;
  mensagem: string;
  dataHora: string;
};

const alertas: Alert[] = [
  {
    id: '1',
    tipo: 'critico',
    titulo: 'UTI Fechada para Admissoes',
    mensagem: 'Taxa de ocupacao atingiu 100%. Novas admissoes suspensas.',
    dataHora: '2025-11-18 15:30',
  },
  {
    id: '2',
    tipo: 'aviso',
    titulo: 'Alta Aguardando Destino',
    mensagem: 'Paciente 456789 no Leito 03 aguarda definicao do NIR ha 4 horas.',
    dataHora: '2025-11-18 14:15',
  },
  {
    id: '3',
    tipo: 'info',
    titulo: 'Nova Solicitacao de Vaga',
    mensagem: 'BC solicitou vaga cirurgica para paciente 123456.',
    dataHora: '2025-11-18 13:45',
  },
  {
    id: '4',
    tipo: 'critico',
    titulo: 'Sinalizacao de Transferencia',
    mensagem: 'Leito 08 marcado para transferencia urgente.',
    dataHora: '2025-11-18 12:00',
  },
  {
    id: '5',
    tipo: 'aviso',
    titulo: 'Tempo de Higienizacao Excedido',
    mensagem: 'Leito 12 em higienizacao ha mais de 2 horas.',
    dataHora: '2025-11-18 11:30',
  },
];

const alertConfig: Record<
  AlertType,
  {
    icon: any;
    iconColor: string;
    badgeClass: string;
    cardClass: string;
    iconBg: string;
  }
> = {
  critico: {
    icon: ExclamationTriangleIcon,
    iconColor: 'text-red-600',
    badgeClass: 'border border-red-200 bg-red-100 text-red-800',
    cardClass: 'border-red-100 bg-red-50',
    iconBg: 'bg-red-100',
  },
  aviso: {
    icon: ExclamationCircleIcon,
    iconColor: 'text-amber-600',
    badgeClass: 'border border-amber-200 bg-amber-100 text-amber-800',
    cardClass: 'border-amber-100 bg-amber-50',
    iconBg: 'bg-amber-100',
  },
  info: {
    icon: InformationCircleIcon,
    iconColor: 'text-blue-600',
    badgeClass: 'border border-blue-200 bg-blue-100 text-blue-800',
    cardClass: 'border-blue-100 bg-blue-50',
    iconBg: 'bg-blue-100',
  },
};

const formatTipo = (tipo: AlertType) => tipo.charAt(0).toUpperCase() + tipo.slice(1);
</script>
