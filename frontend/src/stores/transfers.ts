import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Transfer } from '../types/care';
import { listTransfers, createTransfer, approveTransfer, denyTransfer, buildLocalTransfer } from '../services/transfers';
import { useToast } from 'vue-toastification';
import { useBedsStore } from './beds';
import { useRoleStore } from './role';

export const useTransfersStore = defineStore('transfers', () => {
  const transfers = ref<Transfer[]>([]);
  const localCreated = ref<Transfer[]>([]);
  const toast = useToast();
  const roleStore = useRoleStore();
  const bedsStore = useBedsStore();

  const pending = computed(() => transfers.value.filter(t => t.status === 'PENDENTE'));
  const visibleTransfers = computed(() =>
    roleStore.role === 'SURGICAL_CENTER' ? localCreated.value : transfers.value
  );

  async function load() {
    if (roleStore.role === 'ICU') {
      transfers.value = await listTransfers(roleStore.role);
      return;
    }
    transfers.value = [];
  }

  async function syncAfterMutation(options?: { beds?: boolean }) {
    const tasks: Array<Promise<unknown>> = [load()];
    if (options?.beds && roleStore.role === 'ICU') {
      tasks.push(bedsStore.load());
    }
    await Promise.all(tasks);
  }

  async function create(payload: { prontuario_paciente: number; idade_paciente: number; especialidade_paciente: string }) {
    await createTransfer(payload);
    localCreated.value = [buildLocalTransfer(payload), ...localCreated.value];
    toast.success('Solicitação de transferência enviada.');
    await syncAfterMutation();
  }

  async function decide(transferId: number, decision: 'ACCEPT' | 'DENY', bedId?: string | null) {
    if (decision === 'ACCEPT') {
      if (!bedId) {
        throw new Error('Selecione um leito para aceitar a transferência.');
      }
      await approveTransfer(transferId, bedId);
      toast.success('Transferência aceita.');
    } else {
      await denyTransfer(transferId);
      toast.success('Transferência negada.');
    }
    await syncAfterMutation({ beds: true });
  }

  return {
    transfers,
    localCreated,
    pending,
    visibleTransfers,
    load,
    create,
    decide,
  };
});
