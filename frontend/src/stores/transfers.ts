import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Transfer } from '../types/care';
import { listTransfers, createTransfer, decideTransfer } from '../services/transfers';
import { useToast } from 'vue-toastification';
import { useBedsStore } from './beds';
import { useNotificationsStore } from './notifications';
import { useRoleStore } from './role';

export const useTransfersStore = defineStore('transfers', () => {
  const transfers = ref<Transfer[]>([]);
  const toast = useToast();
  const roleStore = useRoleStore();
  const bedsStore = useBedsStore();
  const notificationsStore = useNotificationsStore();

  const pending = computed(() => transfers.value.filter(t => t.status === 'PENDENTE'));

  async function load() {
    transfers.value = await listTransfers(roleStore.role);
  }

  async function syncAfterMutation(options?: { beds?: boolean }) {
    const tasks: Array<Promise<unknown>> = [
      load(),
      notificationsStore.load(roleStore.role, true),
    ];
    if (options?.beds) {
      tasks.push(bedsStore.load());
    }
    await Promise.all(tasks);
  }

  async function create(payload: { patientId: string; reservationId?: number | null; bedId?: number | null; notes?: string | null }) {
    const tr = await createTransfer(payload);
    toast.success('Solicitação de transferência enviada para UTI.');
    await syncAfterMutation();
    return tr;
  }

  async function decide(transferId: number, decision: 'ACCEPT' | 'DENY', bedId?: number | null) {
    const tr = await decideTransfer(transferId, decision, bedId);
    toast.success(decision === 'ACCEPT' ? 'Transferência aceita.' : 'Transferência negada.');
    await syncAfterMutation({ beds: true });
    return tr;
  }

  return {
    transfers,
    pending,
    load,
    create,
    decide,
  };
});
