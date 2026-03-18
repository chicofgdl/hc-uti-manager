// Fora do contrato atual do YAML.
// Este store nao deve ser reativado sem definicao explicita do backend.
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Notification, Role } from '../types/care';
import { fetchNotifications, markAllRead, markNotificationRead } from '../services/notifications';

const POLL_INTERVAL_MS = 10000;

export const useNotificationsStore = defineStore('notifications', () => {
  const notifications = ref<Notification[]>([]);
  const unreadCount = computed(() => notifications.value.filter(n => !n.read).length);
  let interval: ReturnType<typeof setInterval> | null = null;

  async function load(role: Role, unreadOnly = false) {
    notifications.value = await fetchNotifications(role, unreadOnly);
  }

  async function markRead(id: number) {
    const updated = await markNotificationRead(id);
    notifications.value = notifications.value.map(n => (n.id === id ? updated : n));
  }

  async function markAll(role: Role) {
    await markAllRead(role);
    notifications.value = notifications.value.map(n => ({ ...n, read: true }));
  }

  function startPolling(role: Role) {
    stopPolling();
    load(role, true);
    interval = setInterval(() => load(role, true), POLL_INTERVAL_MS);
  }

  function stopPolling() {
    if (interval) {
      clearInterval(interval);
      interval = null;
    }
  }

  return {
    notifications,
    unreadCount,
    load,
    markRead,
    markAll,
    startPolling,
    stopPolling,
  };
});
