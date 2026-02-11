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

export const useReservationsStore = defineStore('reservations', () => {
  const reservations = ref<Reservation[]>([]);
  const toast = useToast();

  const pending = computed(() => reservations.value.filter(r => r.status === 'PENDENTE'));
  const accepted = computed(() => reservations.value.filter(r => r.status === 'ACEITA'));

  async function load() {
    const data = await listReservations();
    reservations.value = data;
  }

  async function create(payload: { patientId: string; notes?: string; preferredDateTime?: string | null }) {
    const res = await createReservation(payload);
    toast.success('Solicitação de reserva enviada ao UTI.');
    await load();
    return res;
  }

  async function decide(reservationId: number, decision: 'ACCEPT' | 'DENY', bedId?: number | null) {
    const res = await decideReservation(reservationId, decision, bedId);
    toast.success(decision === 'ACCEPT' ? 'Reserva aceita.' : 'Reserva negada.');
    await load();
    return res;
  }

  async function cancelByCc(reservationId: number, reason?: string) {
    const res = await cancelReservationCc(reservationId, reason);
    toast.info('Reserva cancelada pelo CC.');
    await load();
    return res;
  }

  async function cancelByIcu(reservationId: number, reason?: string) {
    const res = await cancelReservationIcu(reservationId, reason);
    toast.info('Reserva cancelada pela UTI.');
    await load();
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
