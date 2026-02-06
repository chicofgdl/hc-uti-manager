<template>
  <section class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="text-3xl font-bold text-slate-900">Alertas e notificações</h2>
        <p class="text-sm text-slate-600">Exibindo notificações do papel {{ roleStore.role }}.</p>
      </div>
      <div class="flex gap-2">
        <UiButton variant="outline" size="sm" @click="reload">Recarregar</UiButton>
        <UiButton size="sm" @click="markAll">Marcar todas como lidas</UiButton>
      </div>
    </div>

    <div class="flex gap-2">
      <UiButton
        v-for="opt in filters"
        :key="opt.value"
        :variant="filter === opt.value ? 'default' : 'outline'"
        size="sm"
        @click="filter = opt.value"
      >
        {{ opt.label }}
      </UiButton>
    </div>

    <div class="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div class="divide-y divide-slate-100">
        <div
          v-for="notif in filteredNotifications"
          :key="notif.id"
          class="px-4 py-3 flex items-start gap-3 hover:bg-slate-50 transition"
        >
          <div
            class="rounded-full p-2"
            :class="notif.read ? 'bg-slate-100 text-slate-400' : typeConfig[notif.type].bg"
          >
            <component :is="typeConfig[notif.type].icon" class="h-5 w-5" />
          </div>
          <div class="flex-1">
            <div class="flex items-center justify-between gap-2">
              <p class="font-semibold text-slate-900">{{ typeConfig[notif.type].title }}</p>
              <UiBadge :class="notif.read ? 'bg-slate-100 text-slate-500 border-slate-200' : typeConfig[notif.type].badge">
                {{ notif.type }}
              </UiBadge>
            </div>
            <p class="text-sm text-slate-700 mt-1">{{ notif.message }}</p>
            <p class="text-xs text-slate-500 mt-1">{{ formatDate(notif.created_at) }}</p>
          </div>
          <UiButton
            size="xs"
            variant="outline"
            :disabled="notif.read"
            @click="markRead(notif.id)"
          >
            {{ notif.read ? 'Lida' : 'Marcar como lida' }}
          </UiButton>
        </div>
        <p v-if="filteredNotifications.length === 0" class="px-4 py-6 text-sm text-slate-500">
          Nenhuma notificação encontrada.
        </p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import UiButton from '../components/ui/Button.vue';
import UiBadge from '../components/ui/Badge.vue';
import { useNotificationsStore } from '../stores/notifications';
import { useRoleStore } from '../stores/role';
import { Bell, FileText, ArrowRightLeft, LogOut } from 'lucide-vue-next';

const notificationsStore = useNotificationsStore();
const roleStore = useRoleStore();

const filters = [
  { value: 'all', label: 'Todas' },
  { value: 'unread', label: 'Não lidas' },
];
const filter = ref<'all' | 'unread'>('all');

const typeConfig = {
  RESERVA_CRIADA: { icon: Bell, bg: 'bg-emerald-50 text-emerald-700', title: 'Reserva criada', badge: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  RESERVA_ATUALIZADA: { icon: FileText, bg: 'bg-blue-50 text-blue-700', title: 'Reserva atualizada', badge: 'bg-blue-50 text-blue-700 border-blue-200' },
  TRANSFERENCIA_CRIADA: { icon: ArrowRightLeft, bg: 'bg-amber-50 text-amber-700', title: 'Transferência solicitada', badge: 'bg-amber-50 text-amber-700 border-amber-200' },
  TRANSFERENCIA_ATUALIZADA: { icon: LogOut, bg: 'bg-purple-50 text-purple-700', title: 'Transferência atualizada', badge: 'bg-purple-50 text-purple-700 border-purple-200' },
};

const reload = () => {
  notificationsStore.load(roleStore.role, filter.value === 'unread');
};

const markRead = async (id: number) => {
  await notificationsStore.markRead(id);
};

const markAll = async () => {
  await notificationsStore.markAll(roleStore.role);
};

const filteredNotifications = computed(() =>
  filter.value === 'unread'
    ? notificationsStore.notifications.filter(n => !n.read)
    : notificationsStore.notifications
);

const formatDate = (value: string) => new Date(value).toLocaleString('pt-BR', { hour12: false });

onMounted(() => {
  reload();
  notificationsStore.startPolling(roleStore.role);
});

watch(
  () => roleStore.role,
  () => {
    notificationsStore.startPolling(roleStore.role);
    reload();
  }
);

watch(filter, () => reload());
</script>
