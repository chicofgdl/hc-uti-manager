<template>
  <div class="relative">
    <button @click="isOpen = !isOpen" class="relative z-10 block h-10 w-10 rounded-full overflow-hidden border-2 border-gray-600 focus:outline-none focus:border-white">
      <UserCircleIcon class="h-full w-full text-gray-600" />
    </button>

    <div v-if="isOpen" @click="isOpen = false" class="fixed inset-0 h-full w-full z-10"></div>

    <div v-if="isOpen" class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-xl z-20">
      <div v-if="authStore.isAuthenticated" class="py-2">
        <div class="px-4 py-2 text-sm text-gray-700">
          <p class="font-semibold">{{ authStore.user?.username || 'User' }}</p>
          <p class="text-xs text-gray-500 truncate">{{ authStore.user?.username || 'No AD User' }}</p>
        </div>
        <div class="border-t border-gray-200"></div>
        <a href="#" @click.prevent="handleLogout" class="block px-4 py-2 text-sm text-gray-700 hover:bg-blue-500 hover:text-white">Logout</a>
      </div>
      <div v-else class="py-2">
        <router-link to="/login" class="block px-4 py-2 text-sm text-gray-700 hover:bg-blue-500 hover:text-white">Login</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { UserCircleIcon } from '@heroicons/vue/24/solid';
import { useAuthStore } from '../stores/auth';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const isOpen = ref(false);

const handleLogout = async () => {
  await authStore.logout();
  // Navigation is now handled by the component after the store action completes
  router.push('/login');
};

// Close dropdown on navigation
watch(() => route.path, () => {
  isOpen.value = false;
});
</script>
