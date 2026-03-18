import { createRouter, createWebHistory, NavigationGuardNext } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import Home from '../views/Home.vue';
import Login from '../views/Login.vue';
import Admin from '../views/Admin.vue';

import Exemplos from '../views/Exemplos.vue';
import Pacientes from '../views/Pacientes.vue';
import Solicitacoes from '../views/Solicitacoes.vue';
import Altas from '../views/Altas.vue';
import Indicadores from '../views/Indicadores.vue';
import Historico from '../views/Historico.vue';
import ApiYamlTester from '../views/ApiYamlTester.vue';

const routes = [
  {
    path: '/',
    name: 'Leitos',
    component: Home,
    meta: { title: 'Gestao de Leitos da UTI' },
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { layout: 'LoginLayout' },
  },
  {
    path: '/admin',
    name: 'Admin',
    component: Admin,
    meta: { requiresAuth: true },
  },

  {
    path: '/exemplos',
    name: 'Exemplos',
    component: Exemplos,
  },
  {
    path: '/pacientes',
    name: 'Pacientes',
    component: Pacientes,
    meta: { requiresAuth: true },
  },
  {
    path: '/solicitacoes',
    name: 'Solicitacoes',
    component: Solicitacoes,
    meta: { title: 'Reservas de Leito' },
  },
  {
    path: '/altas',
    name: 'Altas',
    component: Altas,
    meta: { title: 'Transferencias' },
  },
  {
    path: '/indicadores',
    name: 'Indicadores',
    component: Indicadores,
    meta: { title: 'Indicadores Operacionais' },
  },
  {
    path: '/historico',
    name: 'Historico',
    component: Historico,
    meta: { title: 'Historico de Acoes' },
  },
  {
    path: '/teste-api',
    name: 'ApiTeste',
    component: ApiYamlTester,
    meta: { title: 'Teste das Rotas do YAML' },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  linkActiveClass: 'bg-paper-active-link',
  linkExactActiveClass: 'bg-paper-active-link',
});

router.beforeEach((to, _from, next: NavigationGuardNext) => {
  const authStore = useAuthStore();
  const isLoginRoute = to.name === 'Login';

  if (!authStore.isAuthenticated && !isLoginRoute) {
    next({ name: 'Login', query: { redirect: to.fullPath } });
    return;
  }

  if (authStore.isAuthenticated && isLoginRoute) {
    next({ name: 'Leitos' });
    return;
  }

  next();
});

export default router;
