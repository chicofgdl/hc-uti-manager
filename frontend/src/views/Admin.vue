<template>
  <Card>
    <div v-if="authStore.isAdmin">
      <h1 class="text-2xl font-bold text-green-600">Admin Area</h1>
      <p class="mt-4">Welcome, administrator! This content is only visible to users with admin privileges.</p>
      <!-- Further admin-only content or API calls can go here -->
      <div v-if="adminData" class="mt-6 p-4 bg-gray-100 rounded">
        <h3 class="font-bold">Admin Data (Example):</h3>
        <pre class="text-sm whitespace-pre-wrap">{{ adminData }}</pre>
      </div>
    </div>
    <div v-else>
      <h1 class="text-2xl font-bold text-red-600">Access Denied</h1>
      <p class="mt-4">You do not have sufficient privileges to view this page.</p>
    </div>
  </Card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import Card from '../components/Card.vue';
import { useAuthStore } from '../stores/auth';
import api from '../services/api'; // Assuming you have an axios instance

const authStore = useAuthStore();
const adminData = ref(null);
const error = ref<string | object | null>(null);

onMounted(async () => {
  if (authStore.isAdmin) {
    // Example of fetching admin-only data
    try {
      const response = await api.get('/api/admin-only-data'); // This endpoint needs to be created on backend
      adminData.value = response.data;
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || 'Failed to fetch admin data';
      console.error("Error fetching admin data:", error.value);
    }
  }
});
</script>
