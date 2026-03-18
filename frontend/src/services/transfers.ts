import api from './api';
import { Transfer, Role } from '../types/care';

type LegacyTransfer = {
  id: number;
  status: string;
  prontuario_paciente?: number | null;
  idade_paciente?: number | null;
  especialidade_paciente?: string | null;
  leito_id?: string | null;
  solicitada_em?: string | null;
  atualizada_em?: string | null;
  motivo_negacao?: string | null;
};

const normalizeStatus = (value: string): Transfer['status'] => {
  if (value === 'APROVADA' || value === 'ACEITA') return 'ACEITA';
  if (value === 'NEGADA') return 'NEGADA';
  if (value === 'CANCELADA') return 'CANCELADA';
  return 'PENDENTE';
};

const toTransfer = (item: LegacyTransfer, requestedBy?: Role, source: 'yaml' | 'mock-local' = 'yaml'): Transfer => {
  const prontuario = item.prontuario_paciente ?? null;
  return {
    id: item.id,
    status: normalizeStatus(item.status),
    patient: {
      id: prontuario ? Number(prontuario) : item.id,
      external_id: prontuario ? String(prontuario) : `mock-${item.id}`,
      name: item.especialidade_paciente || null,
    },
    bed_code: item.leito_id ?? null,
    requested_by: requestedBy,
    created_at: item.solicitada_em || new Date().toISOString(),
    updated_at: item.atualizada_em || new Date().toISOString(),
    prontuario_paciente: prontuario ? Number(prontuario) : null,
    idade_paciente: item.idade_paciente ?? null,
    especialidade_paciente: item.especialidade_paciente ?? null,
    motivo_negacao: item.motivo_negacao ?? null,
    source,
  };
};

export async function listTransfers(role: Role): Promise<Transfer[]> {
  if (role !== 'ICU') {
    return [];
  }
  const { data } = await api.get('/transferencias');
  return Array.isArray(data)
    ? data.map((item) => toTransfer(item as LegacyTransfer, 'SURGICAL_CENTER'))
    : [];
}

export async function createTransfer(payload: { prontuario_paciente: number; idade_paciente: number; especialidade_paciente: string }): Promise<void> {
  await api.post('/transferencias', payload);
}

export async function approveTransfer(transferId: number, leitoId: string): Promise<void> {
  await api.post(`/transferencias/${transferId}/aceitar`, {
    leito_id: leitoId,
  });
}

export async function denyTransfer(transferId: number, motivo?: string): Promise<void> {
  await api.post(`/transferencias/${transferId}/negar`, motivo ? { motivo } : {});
}

export function buildLocalTransfer(payload: { prontuario_paciente: number; idade_paciente: number; especialidade_paciente: string }): Transfer {
  return toTransfer(
    {
      id: Date.now(),
      status: 'PENDENTE',
      prontuario_paciente: payload.prontuario_paciente,
      idade_paciente: payload.idade_paciente,
      especialidade_paciente: payload.especialidade_paciente,
      solicitada_em: new Date().toISOString(),
      atualizada_em: new Date().toISOString(),
    },
    'SURGICAL_CENTER',
    'mock-local'
  );
}
