<template>
  <component :is="layout">
    <router-view />
  </component>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import DefaultLayout from './layouts/DefaultLayout.vue';
import LoginLayout from './layouts/LoginLayout.vue';
import { useAuthStore } from './stores/auth';

const route = useRoute();
const authStore = useAuthStore();

onMounted(() => {
  authStore.initializeAuth();
});

const layout = computed(() => {
  switch (route.meta.layout) {
    case 'LoginLayout':
      return LoginLayout;
    default:
      return DefaultLayout;
  }
});
</script>
