import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Bed } from '../types/care';
import { fetchBeds, fetchAvailableCount, updateAvailability } from '../services/beds';
import { useToast } from 'vue-toastification';

export const useBedsStore = defineStore('beds', () => {
  const beds = ref<Bed[]>([]);
  const availableCount = ref(0);
  const toast = useToast();

  const availableBeds = computed(() => beds.value.filter(b => b.availability_status === 'DISPONIVEL' && b.occupancy_status === 'LIVRE'));

  async function load() {
    beds.value = await fetchBeds();
    availableCount.value = await fetchAvailableCount();
  }

  async function toggleAvailability(bedId: number, available: boolean) {
    const bed = await updateAvailability(bedId, available);
    beds.value = beds.value.map(b => (b.id === bed.id ? bed : b));
    availableCount.value = await fetchAvailableCount();
    toast.success(available ? 'Leito disponibilizado para reserva.' : 'Leito marcado como não disponível.');
  }

  return {
    beds,
    availableCount,
    availableBeds,
    load,
    toggleAvailability,
  };
});
