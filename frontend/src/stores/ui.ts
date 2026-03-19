import { defineStore } from 'pinia';
import { computed, ref } from 'vue';

export const useUiStore = defineStore('ui', () => {
  const pendingRequests = ref(0);
  const pendingNavigations = ref(0);
  const navigationLabel = ref('');

  const isRequestLoading = computed(() => pendingRequests.value > 0);
  const isRouteLoading = computed(() => pendingNavigations.value > 0);
  const isLoading = computed(() => isRequestLoading.value || isRouteLoading.value);
  const loadingMessage = computed(() => {
    if (isRouteLoading.value) {
      return navigationLabel.value ? `Abrindo ${navigationLabel.value}` : 'Abrindo pagina';
    }

    if (isRequestLoading.value) {
      return 'Atualizando dados';
    }

    return '';
  });

  function startRequestLoading() {
    pendingRequests.value += 1;
  }

  function finishRequestLoading() {
    pendingRequests.value = Math.max(0, pendingRequests.value - 1);
  }

  function startNavigation(label?: string) {
    pendingNavigations.value += 1;
    navigationLabel.value = label ?? '';
  }

  function finishNavigation() {
    pendingNavigations.value = Math.max(0, pendingNavigations.value - 1);

    if (pendingNavigations.value === 0) {
      navigationLabel.value = '';
    }
  }

  return {
    isLoading,
    isRequestLoading,
    isRouteLoading,
    loadingMessage,
    startRequestLoading,
    finishRequestLoading,
    startNavigation,
    finishNavigation,
  };
});
