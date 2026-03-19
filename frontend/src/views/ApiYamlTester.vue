<template>
  <section class="space-y-6">
    <header class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div class="grid gap-3 md:grid-cols-2">
        <label class="space-y-1">
          <span class="text-xs font-semibold uppercase tracking-wide text-slate-500">Base URL</span>
          <input
            v-model="baseUrl"
            type="text"
            class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none transition focus:border-blue-500"
            placeholder="http://localhost:8000"
          />
        </label>
        <label class="space-y-1">
          <span class="text-xs font-semibold uppercase tracking-wide text-slate-500">Bearer Token (opcional)</span>
          <input
            v-model="bearerToken"
            type="text"
            class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none transition focus:border-blue-500"
            placeholder="cole aqui o access token"
          />
        </label>
      </div>

      <div class="mt-3 flex flex-wrap items-center gap-2">
        <button
          class="rounded-lg bg-blue-600 px-3 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="isRunningAny"
          @click="runAllTests"
        >
          Executar todos
        </button>
        <span class="text-xs text-slate-500">
          Cada item mostra requisicao, payload exemplo e retorno bruto da API.
        </span>
      </div>
    </header>

    <div class="space-y-3">
      <details
        v-for="endpoint in endpoints"
        :key="endpoint.id"
        class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
      >
        <summary class="cursor-pointer list-none">
          <div class="flex flex-wrap items-center gap-2">
            <span
              class="rounded-md px-2 py-1 text-xs font-bold uppercase"
              :class="methodClass(endpoint.method)"
            >
              {{ endpoint.method }}
            </span>
            <code class="text-sm font-semibold text-slate-800">{{ endpoint.path }}</code>
            <span
              v-if="endpoint.result"
              class="rounded-md px-2 py-1 text-xs font-semibold"
              :class="endpoint.result.ok ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'"
            >
              {{ endpoint.result.ok ? 'Funcionando' : 'Nao funcionando' }}
            </span>
            <span v-if="endpoint.running" class="text-xs font-semibold text-blue-600">Testando...</span>
          </div>
          <p class="mt-2 text-sm text-slate-600">{{ endpoint.summary }}</p>
        </summary>

        <div class="mt-4 space-y-3 border-t border-slate-100 pt-4">
          <div class="grid gap-3 md:grid-cols-2">
            <div>
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Codigo esperado</p>
              <p class="mt-1 text-sm font-semibold text-slate-700">{{ endpoint.expectedStatuses.join(', ') }}</p>
            </div>
            <div>
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Retorno esperado</p>
              <p class="mt-1 text-sm text-slate-700">{{ endpoint.responseHint }}</p>
            </div>
          </div>

          <div v-if="endpoint.pathParamsText" class="space-y-1">
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Path params (JSON)</p>
            <textarea
              v-model="endpoint.pathParamsText"
              rows="4"
              class="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-xs outline-none transition focus:border-blue-500"
            />
          </div>

          <div v-if="endpoint.method !== 'GET' && endpoint.method !== 'DELETE'" class="space-y-1">
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Body exemplo ({{ endpoint.contentType === 'form' ? 'JSON para form-urlencoded' : 'JSON' }})
            </p>
            <textarea
              v-model="endpoint.bodyText"
              rows="6"
              class="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-xs outline-none transition focus:border-blue-500"
            />
          </div>

          <div class="flex flex-wrap items-center gap-3">
            <button
              class="rounded-lg bg-slate-900 px-3 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="endpoint.running"
              @click="runSingleTest(endpoint)"
            >
              Testar rota
            </button>
            <span
              v-if="endpoint.result"
              class="text-xs font-semibold"
              :class="endpoint.result.ok ? 'text-emerald-700' : 'text-rose-700'"
            >
              HTTP {{ endpoint.result.statusLabel }} | {{ endpoint.result.durationMs }}ms
            </span>
          </div>

          <div v-if="endpoint.result" class="space-y-1">
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Resposta</p>
            <pre class="max-h-80 overflow-auto rounded-lg bg-slate-900 p-3 text-xs text-slate-100">{{ endpoint.result.responseText }}</pre>
          </div>
        </div>
      </details>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useAuthStore } from '../stores/auth';

type HttpMethod = 'GET' | 'POST' | 'DELETE';
type BodyType = 'json' | 'form';

interface EndpointConfig {
  id: string;
  method: HttpMethod;
  path: string;
  summary: string;
  expectedStatuses: number[];
  responseHint: string;
  requiresAuth: boolean;
  contentType?: BodyType;
  samplePathParams?: Record<string, string | number>;
  sampleBody?: Record<string, unknown>;
}

interface EndpointResult {
  ok: boolean;
  status: number | null;
  statusLabel: string;
  durationMs: number;
  responseText: string;
}

interface EndpointState extends EndpointConfig {
  pathParamsText: string;
  bodyText: string;
  running: boolean;
  result: EndpointResult | null;
}

const endpointConfigs: EndpointConfig[] = [
  { id: 'login', method: 'POST', path: '/api/login', summary: 'Login (form)', expectedStatuses: [200], responseHint: 'Token de acesso retornado', requiresAuth: false, contentType: 'form', sampleBody: { username: 'admin', password: 'admin', remember_me: false } },
  { id: 'refresh', method: 'POST', path: '/api/token/refresh', summary: 'Refresh access token usando cookie', expectedStatuses: [200], responseHint: 'Novo access token', requiresAuth: false },
  { id: 'logout', method: 'POST', path: '/api/logout', summary: 'Logout (invalida refresh token cookie)', expectedStatuses: [200], responseHint: 'Logout realizado', requiresAuth: false },
  { id: 'users-me', method: 'GET', path: '/api/users/me', summary: 'Get current user', expectedStatuses: [200], responseHint: 'Dados do usuario', requiresAuth: true },
  { id: 'admin-data', method: 'GET', path: '/api/admin-only-data', summary: 'Dados apenas para admin', expectedStatuses: [200], responseHint: 'Dados sensiveis do admin', requiresAuth: true },
  { id: 'pacientes-list', method: 'GET', path: '/api/pacientes', summary: 'Listar pacientes', expectedStatuses: [200], responseHint: 'Lista de pacientes', requiresAuth: true },
  { id: 'pacientes-get', method: 'GET', path: '/api/pacientes/{codigo}', summary: 'Obter paciente por codigo', expectedStatuses: [200], responseHint: 'Paciente', requiresAuth: true, samplePathParams: { codigo: 77001 } },
  { id: 'pacientes-quantidade', method: 'GET', path: '/api/pacientes/disponiveis/quantidade', summary: 'Quantidade de leitos disponiveis via pacientes', expectedStatuses: [200], responseHint: 'Quantidade disponivel', requiresAuth: true },
  { id: 'leitos-list', method: 'GET', path: '/leitos', summary: 'Listar leitos', expectedStatuses: [200], responseHint: 'Lista de leitos', requiresAuth: true },
  { id: 'leito-reservar', method: 'POST', path: '/leitos/{lto_lto_id}/reservar', summary: 'Reservar leito', expectedStatuses: [200], responseHint: 'Reserva executada', requiresAuth: true, contentType: 'json', samplePathParams: { lto_lto_id: '0803A' }, sampleBody: { prontuario: 77001, idade: 40, especialidade: 'Cardiologia' } },
  { id: 'leito-alta-solicitar', method: 'POST', path: '/leitos/{leito_id}/alta', summary: 'Solicitar alta', expectedStatuses: [204], responseHint: 'Alta solicitada', requiresAuth: true, samplePathParams: { leito_id: '0803A' } },
  { id: 'leito-alta-cancelar', method: 'DELETE', path: '/leitos/{leito_id}/alta', summary: 'Cancelar alta', expectedStatuses: [204], responseHint: 'Alta cancelada', requiresAuth: true, samplePathParams: { leito_id: '0803A' } },
  { id: 'leitos-disponiveis', method: 'GET', path: '/leitos/disponiveis-para-reserva', summary: 'Listar leitos disponiveis para reserva', expectedStatuses: [200], responseHint: 'Lista de leitos disponiveis', requiresAuth: true },
  { id: 'leitos-quantidade', method: 'GET', path: '/leitos/quantidade-disponiveis', summary: 'Quantidade de leitos disponiveis', expectedStatuses: [200], responseHint: 'Quantidade de leitos disponiveis', requiresAuth: true },
  { id: 'solicitacoes-criar', method: 'POST', path: '/solicitacoes-reserva', summary: 'Criar solicitacao de reserva', expectedStatuses: [201], responseHint: 'Solicitacao criada', requiresAuth: true, contentType: 'json', sampleBody: { prontuario: '77001', idade: 40, especialidade: 'Cardiologia' } },
  { id: 'solicitacoes-listar', method: 'GET', path: '/solicitacoes-reserva', summary: 'Listar todas solicitacoes', expectedStatuses: [200], responseHint: 'Lista de solicitacoes', requiresAuth: true },
  { id: 'solicitacoes-pendentes', method: 'GET', path: '/solicitacoes-reserva/pendentes', summary: 'Listar solicitacoes pendentes', expectedStatuses: [200], responseHint: 'Lista pendentes', requiresAuth: true },
  { id: 'solicitacoes-aprovar', method: 'POST', path: '/solicitacoes-reserva/{id}/aprovar', summary: 'Aprovar solicitacao', expectedStatuses: [200], responseHint: 'Solicitacao aprovada', requiresAuth: true, contentType: 'json', samplePathParams: { id: 1 }, sampleBody: { lto_lto_id: '0803A' } },
  { id: 'solicitacoes-negar', method: 'POST', path: '/solicitacoes-reserva/{id}/negar', summary: 'Negar solicitacao', expectedStatuses: [200], responseHint: 'Solicitacao negada', requiresAuth: true, contentType: 'json', samplePathParams: { id: 1 }, sampleBody: { motivo: 'Sem leito' } },
  { id: 'solicitacoes-cancelar', method: 'POST', path: '/solicitacoes-reserva/{id}/cancelar', summary: 'Cancelar solicitacao', expectedStatuses: [200], responseHint: 'Solicitacao cancelada', requiresAuth: true, contentType: 'json', samplePathParams: { id: 1 }, sampleBody: { motivo: 'Paciente recebeu alta' } },
  { id: 'reservas-criar', method: 'POST', path: '/reservas', summary: 'Criar reserva', expectedStatuses: [201], responseHint: 'Reserva criada', requiresAuth: true, contentType: 'json', sampleBody: { prontuario: '77001', idade: 40, especialidade: 'Cardiologia' } },
  { id: 'transferencias-criar', method: 'POST', path: '/transferencias', summary: 'Criar transferencia', expectedStatuses: [200], responseHint: 'Transferencia criada', requiresAuth: true, contentType: 'json', sampleBody: { prontuario_paciente: 77001, idade_paciente: 40, especialidade_paciente: 'Cardiologia' } },
  { id: 'transferencias-listar', method: 'GET', path: '/transferencias', summary: 'Listar transferencias', expectedStatuses: [200], responseHint: 'Lista de transferencias', requiresAuth: true },
  { id: 'transferencias-aceitar', method: 'POST', path: '/transferencias/{transferencia_id}/aceitar', summary: 'Aceitar transferencia', expectedStatuses: [200], responseHint: 'Transferencia aceita', requiresAuth: true, contentType: 'json', samplePathParams: { transferencia_id: 1 }, sampleBody: { leito_id: '0803A' } },
  { id: 'transferencias-negar', method: 'POST', path: '/transferencias/{transferencia_id}/negar', summary: 'Negar transferencia', expectedStatuses: [200], responseHint: 'Transferencia negada', requiresAuth: true, contentType: 'json', samplePathParams: { transferencia_id: 1 }, sampleBody: { motivo: 'Sem vaga' } },
];

const authStore = useAuthStore();
const baseUrl = ref('http://localhost:8000');
const bearerToken = ref(authStore.accessToken ?? '');

const endpoints = ref<EndpointState[]>(
  endpointConfigs.map((item) => ({
    ...item,
    pathParamsText: item.samplePathParams ? JSON.stringify(item.samplePathParams, null, 2) : '',
    bodyText: item.sampleBody ? JSON.stringify(item.sampleBody, null, 2) : '',
    running: false,
    result: null,
  })),
);

const isRunningAny = computed(() => endpoints.value.some((item) => item.running));

const methodClass = (method: HttpMethod) => {
  if (method === 'GET') return 'bg-emerald-100 text-emerald-700';
  if (method === 'POST') return 'bg-blue-100 text-blue-700';
  return 'bg-amber-100 text-amber-700';
};

const normalizeBaseUrl = (url: string) => url.replace(/\/+$/, '');

const parseObject = (raw: string, fieldLabel: string): Record<string, unknown> => {
  if (!raw.trim()) return {};
  try {
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      return parsed as Record<string, unknown>;
    }
    throw new Error(`${fieldLabel} deve ser um objeto JSON.`);
  } catch (error) {
    const message = error instanceof Error ? error.message : `JSON invalido em ${fieldLabel}.`;
    throw new Error(message);
  }
};

const formatResponse = (text: string): string => {
  if (!text) return '(sem corpo)';
  try {
    return JSON.stringify(JSON.parse(text), null, 2);
  } catch {
    return text;
  }
};

const resolvePath = (pathTemplate: string, pathParams: Record<string, unknown>) => {
  return pathTemplate.replace(/\{([^}]+)\}/g, (_segment, key: string) => {
    const value = pathParams[key];
    return encodeURIComponent(String(value ?? `{${key}}`));
  });
};

const buildFormBody = (bodyObject: Record<string, unknown>) => {
  const params = new URLSearchParams();
  Object.entries(bodyObject).forEach(([key, value]) => {
    params.append(key, String(value));
  });
  return params;
};

const runSingleTest = async (endpoint: EndpointState) => {
  endpoint.running = true;
  const start = performance.now();

  try {
    const pathParams = parseObject(endpoint.pathParamsText, `Path params de ${endpoint.path}`);
    const resolvedPath = resolvePath(endpoint.path, pathParams);
    const url = `${normalizeBaseUrl(baseUrl.value)}${resolvedPath}`;

    const headers: HeadersInit = {};
    if (endpoint.requiresAuth && bearerToken.value.trim()) {
      headers.Authorization = `Bearer ${bearerToken.value.trim()}`;
    }

    let body: BodyInit | undefined;
    if (endpoint.method !== 'GET' && endpoint.method !== 'DELETE') {
      const bodyObject = parseObject(endpoint.bodyText, `Body de ${endpoint.path}`);
      if (endpoint.contentType === 'form') {
        headers['Content-Type'] = 'application/x-www-form-urlencoded';
        body = buildFormBody(bodyObject);
      } else {
        headers['Content-Type'] = 'application/json';
        body = JSON.stringify(bodyObject);
      }
    }

    const response = await fetch(url, {
      method: endpoint.method,
      headers,
      body,
      credentials: 'include',
    });
    const responseText = await response.text();
    const elapsed = Math.round(performance.now() - start);
    const ok = endpoint.expectedStatuses.includes(response.status);

    endpoint.result = {
      ok,
      status: response.status,
      statusLabel: String(response.status),
      durationMs: elapsed,
      responseText: formatResponse(responseText),
    };
  } catch (error) {
    const elapsed = Math.round(performance.now() - start);
    endpoint.result = {
      ok: false,
      status: null,
      statusLabel: 'erro',
      durationMs: elapsed,
      responseText: error instanceof Error ? error.message : 'Erro inesperado ao executar teste.',
    };
  } finally {
    endpoint.running = false;
  }
};

const runAllTests = async () => {
  for (const endpoint of endpoints.value) {
    // Sequencial para manter o retorno legivel e reduzir efeito colateral em rotas de escrita.
    // eslint-disable-next-line no-await-in-loop
    await runSingleTest(endpoint);
  }
};
</script>
