import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { Role } from '../types/care';

const STORAGE_KEY = 'hc-role';

function deriveRoleFromGroups(groups: string[] = []): Role {
  if (groups.includes('enfermeiro_uti')) {
    return 'ICU';
  }
  if (groups.includes('enfermeiro_cirurgia')) {
    return 'SURGICAL_CENTER';
  }
  return 'ICU';
}

export const useRoleStore = defineStore('role', () => {
  const saved = (localStorage.getItem(STORAGE_KEY) as Role | null) || 'ICU';
  const role = ref<Role>(saved);

  function setRole(value: Role) {
    role.value = value;
    localStorage.setItem(STORAGE_KEY, value);
  }

  function syncFromGroups(groups: string[] = []) {
    setRole(deriveRoleFromGroups(groups));
  }

  function reset() {
    setRole('ICU');
  }

  return { role, setRole, syncFromGroups, reset };
});
