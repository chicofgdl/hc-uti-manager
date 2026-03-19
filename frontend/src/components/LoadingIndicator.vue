<template>
  <Transition name="loading-fade">
    <div
      v-if="shouldRender"
      class="pointer-events-none fixed inset-0 z-50 flex items-start justify-center bg-slate-100/45 px-4 pt-24 backdrop-blur-[2px]"
    >
      <div class="absolute inset-x-0 top-0 h-1 overflow-hidden bg-slate-200/80">
        <div class="loading-bar h-full w-1/3 rounded-full bg-[#1173d4]"></div>
      </div>

      <div class="w-full max-w-sm rounded-2xl border border-slate-200/80 bg-white/95 p-5 shadow-2xl shadow-slate-300/30">
        <div class="flex items-center gap-4">
          <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-100">
            <div class="h-6 w-6 animate-spin rounded-full border-2 border-slate-200 border-t-[#1173d4]"></div>
          </div>

          <div class="space-y-1">
            <p class="text-sm font-semibold text-slate-900">{{ loadingMessage }}</p>
            <p class="text-xs text-slate-500">
              {{ isRouteLoading ? 'Preparando a proxima tela.' : 'Sincronizando informacoes da aplicacao.' }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue';
import { useUiStore } from '../stores/ui';
import { storeToRefs } from 'pinia';

const uiStore = useUiStore();
const { isLoading, isRouteLoading, loadingMessage } = storeToRefs(uiStore);

const shouldRender = ref(false);

let timeoutId: ReturnType<typeof setTimeout> | undefined;

watch(isLoading, (loading) => {
  if (timeoutId) {
    clearTimeout(timeoutId);
    timeoutId = undefined;
  }

  if (loading) {
    timeoutId = setTimeout(() => {
      shouldRender.value = true;
    }, 140);
    return;
  }

  shouldRender.value = false;
});

onBeforeUnmount(() => {
  if (timeoutId) {
    clearTimeout(timeoutId);
  }
});
</script>

<style scoped>
.loading-fade-enter-active,
.loading-fade-leave-active {
  transition: opacity 0.18s ease;
}

.loading-fade-enter-from,
.loading-fade-leave-to {
  opacity: 0;
}

.loading-bar {
  animation: loading-slide 1.2s ease-in-out infinite;
}

@keyframes loading-slide {
  0% {
    transform: translateX(-110%);
  }

  100% {
    transform: translateX(320%);
  }
}
</style>
