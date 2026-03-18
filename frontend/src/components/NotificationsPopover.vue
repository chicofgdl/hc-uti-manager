<!-- Fora do contrato atual do YAML. Componente mantido apenas como referencia, sem uso ativo na navegacao. -->
<template>
  <div class="relative" ref="container">
    <button
      ref="trigger"
      @click.stop="toggle"
      class="relative inline-flex h-10 w-10 items-center justify-center rounded-lg text-slate-600 transition-colors duration-150 hover:bg-blue-500 hover:text-white focus:outline-none focus:ring-2 focus:ring-blue-200"
      aria-label="Abrir notificacoes"
    >
      <Bell class="h-5 w-5" />
      <span
        v-if="unreadCount > 0"
        class="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white shadow"
      >
        {{ unreadCount }}
      </span>
    </button>

    <transition name="fade">
      <div
        v-if="open"
        ref="panel"
        class="absolute right-0 mt-3 w-80 origin-top-right rounded-2xl border border-slate-200 bg-white shadow-xl"
      >
        <div class="flex items-center justify-between border-b border-slate-100 px-4 py-3">
          <h3 class="font-semibold text-slate-900">Notificacoes</h3>
          <button
            class="text-xs font-semibold text-blue-600 hover:underline"
            @click="handleMarkAll"
          >
            Marcar todas como lidas
          </button>
        </div>

        <div class="max-h-96 overflow-auto p-2">
          <div
            v-for="notification in notificationsStore.notifications"
            :key="notification.id"
            class="rounded-lg p-3 transition hover:bg-slate-50"
            :class="!notification.read ? 'bg-blue-50/40' : ''"
            @click="markAsRead(notification.id)"
          >
            <div class="flex gap-3">
              <div
                class="flex h-10 w-10 items-center justify-center rounded-full text-sm font-semibold"
                :class="[typeConfig[notification.type].bg, typeConfig[notification.type].color]"
              >
                <component :is="typeConfig[notification.type].icon" class="h-5 w-5" />
              </div>
              <div class="min-w-0 flex-1">
                <div class="flex items-start justify-between gap-2">
                  <p class="text-sm font-semibold text-slate-900 leading-tight">
                    {{ typeConfig[notification.type].title }}
                  </p>
                  <span
                    v-if="!notification.read"
                    class="mt-1 inline-flex h-2 w-2 shrink-0 rounded-full bg-blue-500"
                    aria-label="Nao lida"
                  />
                </div>
                <p class="mt-1 text-xs text-slate-600 wrap-break-words">{{ notification.message }}</p>
                <div class="mt-2 flex items-center gap-1 text-[11px] text-slate-500">
                  <Clock3 class="h-3 w-3" />
                  <span>{{ formatDate(notification.created_at) }}</span>
                </div>
              </div>
            </div>
          </div>
          <p v-if="notificationsStore.notifications.length === 0" class="px-3 py-2 text-sm text-slate-500">
            Nenhuma notificação.
          </p>
        </div>

        <div class="border-t border-slate-100 p-3">
          <button
            type="button"
            class="w-full rounded-lg px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-blue-50 hover:text-blue-700"
            @click="goToAlerts"
          >
            Ver todas as notificacoes
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import { useRouter } from 'vue-router';
import {
  Bell,
  Clock3,
  FileText,
  LogOut,
  UserPlus,
  ArrowRightLeft,
} from 'lucide-vue-next';
import { useNotificationsStore } from '../stores/notifications';
import { useRoleStore } from '../stores/role';

type NotificationType =
  | 'RESERVA_CRIADA'
  | 'RESERVA_ATUALIZADA'
  | 'TRANSFERENCIA_CRIADA'
  | 'TRANSFERENCIA_ATUALIZADA';

const typeConfig: Record<
  NotificationType,
  {
    icon: any;
    bg: string;
    color: string;
    title: string;
  }
> = {
  RESERVA_CRIADA: {
    icon: UserPlus,
    bg: 'bg-emerald-50',
    color: 'text-emerald-600',
    title: 'Reserva criada',
  },
  RESERVA_ATUALIZADA: {
    icon: FileText,
    bg: 'bg-blue-50',
    color: 'text-blue-600',
    title: 'Reserva atualizada',
  },
  TRANSFERENCIA_CRIADA: {
    icon: ArrowRightLeft,
    bg: 'bg-amber-50',
    color: 'text-amber-600',
    title: 'Transferencia solicitada',
  },
  TRANSFERENCIA_ATUALIZADA: {
    icon: LogOut,
    bg: 'bg-purple-50',
    color: 'text-purple-600',
    title: 'Transferencia atualizada',
  },
};

const notificationsStore = useNotificationsStore();
const roleStore = useRoleStore();

const open = ref(false);
const trigger = ref<HTMLElement | null>(null);
const panel = ref<HTMLElement | null>(null);
const router = useRouter();

const unreadCount = computed(() => notificationsStore.unreadCount);

const toggle = () => {
  open.value = !open.value;
};

const close = () => {
  open.value = false;
};

const markAsRead = async (id: number) => {
  await notificationsStore.markRead(id);
};

const handleMarkAll = async () => {
  await notificationsStore.markAll(roleStore.role);
};

const goToAlerts = () => {
  close();
  router.push('/alertas');
};

const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as Node;
  if (
    !open.value ||
    (trigger.value && trigger.value.contains(target)) ||
    (panel.value && panel.value.contains(target))
  ) {
    return;
  }
  close();
};

const formatDate = (value: string) => {
  return new Date(value).toLocaleString('pt-BR', { hour12: false });
};

onMounted(() => {
  notificationsStore.startPolling(roleStore.role);
  document.addEventListener('click', handleClickOutside);
});

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside);
  notificationsStore.stopPolling();
});

watch(
  () => roleStore.role,
  (role) => {
    notificationsStore.startPolling(role);
  }
);
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease, transform 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
