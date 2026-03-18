import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Reservation } from '../types/care';
import {
  listReservations,
  listPendingReservations,
  createReservation,
  approveReservation,
  denyReservation,
  cancelReservation,
  buildLocalReservation,
} from '../services/reservations';
import { useToast } from 'vue-toastification';
import { useBedsStore } from './beds';
import { useRoleStore } from './role';

export const useReservationsStore = defineStore('reservations', () => {
  const reservations = ref<Reservation[]>([]);
  const localCreated = ref<Reservation[]>([]);
  const toast = useToast();
  const roleStore = useRoleStore();
  const bedsStore = useBedsStore();

  const pending = computed(() => reservations.value.filter(r => r.status === 'PENDENTE'));
  const accepted = computed(() => reservations.value.filter(r => r.status === 'ACEITA'));
  const visibleReservations = computed(() =>
    roleStore.role === 'SURGICAL_CENTER' ? localCreated.value : reservations.value
  );

  async function load() {
    if (roleStore.role === 'ICU') {
      const data = await listReservations(roleStore.role);
      reservations.value = data;
      return;
    }
    reservations.value = [];
  }

  async function syncAfterMutation(options?: { beds?: boolean }) {
    const tasks: Array<Promise<unknown>> = [load()];
    if (roleStore.role === 'ICU') {
      tasks.push(listPendingReservations().then((data) => {
        const merged = new Map<number, Reservation>();
        reservations.value.forEach((item) => merged.set(item.id, item));
        data.forEach((item) => merged.set(item.id, item));
        reservations.value = Array.from(merged.values()).sort((a, b) => b.id - a.id);
      }));
      if (options?.beds) {
        tasks.push(bedsStore.load());
      }
    }
    await Promise.all(tasks);
  }

  async function create(payload: { prontuario: string; idade: number; especialidade: string }) {
    const res = await createReservation(payload);
    localCreated.value = [buildLocalReservation(payload), ...localCreated.value];
    toast.success('Solicitação de reserva enviada.');
    await syncAfterMutation();
    return res;
  }

  async function decide(reservationId: number, decision: 'ACCEPT' | 'DENY', bedId?: string | null) {
    if (decision === 'ACCEPT') {
      if (!bedId) {
        throw new Error('Selecione um leito para aprovar a solicitação.');
      }
      await approveReservation(reservationId, bedId);
      toast.success('Reserva aprovada.');
    } else {
      await denyReservation(reservationId);
      toast.success('Reserva negada.');
    }
    await syncAfterMutation({ beds: true });
  }

  async function cancelByCc(reservationId: number, reason?: string) {
    await cancelReservation(reservationId, reason);
    localCreated.value = localCreated.value.filter((item) => item.id !== reservationId);
    toast.info('Reserva cancelada.');
    await syncAfterMutation();
  }

  async function cancelByIcu(reservationId: number, reason?: string) {
    await cancelReservation(reservationId, reason);
    toast.info('Reserva cancelada pela UTI.');
    await syncAfterMutation({ beds: true });
  }

  return {
    reservations,
    localCreated,
    pending,
    accepted,
    visibleReservations,
    load,
    create,
    decide,
    cancelByCc,
    cancelByIcu,
  };
});
