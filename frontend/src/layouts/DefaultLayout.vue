<template>
  <div class="min-h-screen bg-slate-100 text-slate-900">
    <div class="flex min-h-screen">
      <SidebarNav />

      <div class="flex min-w-0 flex-1 flex-col">
        <header class="sticky top-0 z-20 border-b border-slate-200 bg-white px-6 py-4 shadow-sm">
          <div class="flex items-center justify-between gap-3">
            <div class="space-y-0.5">
              <h1 class="text-xl font-semibold text-slate-900">{{ headerTitle }}</h1>
            </div>
            <div class="flex items-center gap-3">
              <button
                class="relative inline-flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 transition hover:bg-slate-50"
              >
                <BellIcon class="h-5 w-5" />
                <span
                  class="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white shadow"
                >
                  3
                </span>
              </button>
              <router-link
                v-if="!authStore.isAuthenticated"
                to="/login"
                class="rounded-full border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
              >
                Login
              </router-link>
              <ProfileDropdown v-else />
            </div>
          </div>
        </header>

        <main class="flex-1 bg-slate-50 px-5 py-6 md:px-8 md:py-8">
          <router-view />
        </main>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { BellIcon } from '@heroicons/vue/24/outline';
import SidebarNav from '../components/SidebarNav.vue';
import ProfileDropdown from '../components/ProfileDropdown.vue';
import { useAuthStore } from '../stores/auth';

const route = useRoute();
const authStore = useAuthStore();

const headerTitle = computed(() => {
  if (typeof route.meta.title === 'string') {
    return route.meta.title;
  }
  return 'Gestão de Leitos UTI';
});
</script>
