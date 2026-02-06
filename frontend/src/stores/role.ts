import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { Role } from '../types/care';

const STORAGE_KEY = 'hc-role';

export const useRoleStore = defineStore('role', () => {
  const saved = (localStorage.getItem(STORAGE_KEY) as Role | null) || 'ICU';
  const role = ref<Role>(saved);

  function setRole(value: Role) {
    role.value = value;
    localStorage.setItem(STORAGE_KEY, value);
  }

  return { role, setRole };
});
