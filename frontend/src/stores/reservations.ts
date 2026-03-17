import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Reservation } from '../types/care';
import {
  listReservations,
  createReservation,
  decideReservation,
  cancelReservationCc,
  cancelReservationIcu,
} from '../services/reservations';
import { useToast } from 'vue-toastification';
import { useBedsStore } from './beds';
import { useNotificationsStore } from './notifications';
import { useRoleStore } from './role';
import { useTransfersStore } from './transfers';

export const useReservationsStore = defineStore('reservations', () => {
  const reservations = ref<Reservation[]>([]);
  const toast = useToast();
  const roleStore = useRoleStore();
  const bedsStore = useBedsStore();
  const transfersStore = useTransfersStore();
  const notificationsStore = useNotificationsStore();

  const pending = computed(() => reservations.value.filter(r => r.status === 'PENDENTE'));
  const accepted = computed(() => reservations.value.filter(r => r.status === 'ACEITA'));

  async function load() {
    const data = await listReservations(roleStore.role);
    reservations.value = data;
  }

  async function syncAfterMutation(options?: { beds?: boolean; transfers?: boolean }) {
    const tasks: Array<Promise<unknown>> = [
      load(),
      notificationsStore.load(roleStore.role, true),
    ];

    if (options?.beds) {
      tasks.push(bedsStore.load());
    }
    if (options?.transfers) {
      tasks.push(transfersStore.load());
    }

    await Promise.all(tasks);
  }

  async function create(payload: { patientId: string; notes?: string; preferredDateTime?: string | null }) {
    const res = await createReservation(payload);
    toast.success('Solicitação de reserva enviada ao UTI.');
    await syncAfterMutation();
    return res;
  }

  async function decide(reservationId: number, decision: 'ACCEPT' | 'DENY', bedId?: number | null) {
    const res = await decideReservation(reservationId, decision, bedId);
    toast.success(decision === 'ACCEPT' ? 'Reserva aceita.' : 'Reserva negada.');
    await syncAfterMutation({ beds: true });
    return res;
  }

  async function cancelByCc(reservationId: number, reason?: string) {
    const res = await cancelReservationCc(reservationId, reason);
    toast.info('Reserva cancelada pelo CC.');
    await syncAfterMutation({ beds: true, transfers: true });
    return res;
  }

  async function cancelByIcu(reservationId: number, reason?: string) {
    const res = await cancelReservationIcu(reservationId, reason);
    toast.info('Reserva cancelada pela UTI.');
    await syncAfterMutation({ beds: true, transfers: true });
    return res;
  }

  return {
    reservations,
    pending,
    accepted,
    load,
    create,
    decide,
    cancelByCc,
    cancelByIcu,
  };
});
