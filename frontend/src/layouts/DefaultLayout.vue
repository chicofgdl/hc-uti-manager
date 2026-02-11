<template>
  <div class="min-h-screen bg-slate-100 text-slate-900 overflow-hidden">
    <div class="flex h-screen overflow-hidden">
      <SidebarNav :collapsed="sidebarCollapsed" @toggle="toggleSidebar" />

      <div
        class="flex min-w-0 flex-1 flex-col transition-[padding] duration-200"
        :class="sidebarCollapsed ? 'pl-20' : 'pl-64'"
      >
        <header class="sticky top-0 z-20 border-b border-slate-200 bg-white px-6 py-4 shadow-sm">
          <div class="flex items-center justify-between gap-3">
            <div class="space-y-0.5">
              <h1 class="text-xl font-semibold text-slate-900">{{ headerTitle }}</h1>
            </div>
          <div class="flex items-center gap-3">
            <div class="flex items-center rounded-full border border-slate-200 bg-white p-1 text-xs font-semibold text-slate-700 shadow-sm">
              <button
                v-for="option in roleOptions"
                :key="option.value"
                class="rounded-full px-2 py-1 transition"
                :class="roleStore.role === option.value ? 'bg-blue-500 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-50'"
                @click="roleStore.setRole(option.value)"
              >
                {{ option.label }}
              </button>
            </div>
            <NotificationsPopover />
            <ProfileDropdown v-if="authStore.isAuthenticated" />
            <router-link
              v-else
              to="/login"
              class="rounded-full border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
            >
                Login
            </router-link>
          </div>
        </div>
      </header>

        <main class="flex-1 overflow-y-auto bg-slate-50 px-5 py-6 md:px-8 md:py-8">
          <router-view />
        </main>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRoute } from 'vue-router';
import SidebarNav from '../components/SidebarNav.vue';
import ProfileDropdown from '../components/ProfileDropdown.vue';
import NotificationsPopover from '../components/NotificationsPopover.vue';
import { useAuthStore } from '../stores/auth';
import { useRoleStore } from '../stores/role';
import type { Role } from '../types/care';

const route = useRoute();
const authStore = useAuthStore();
const roleStore = useRoleStore();
const sidebarCollapsed = ref(false);

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value;
};

const headerTitle = computed(() => {
  if (typeof route.meta.title === 'string') {
    return route.meta.title;
  }
  return 'Gestão de Leitos UTI';
});

const roleOptions: Array<{ value: Role; label: string }> = [
  { value: 'ICU', label: 'UTI' },
  { value: 'SURGICAL_CENTER', label: 'CC' },
];
</script>
