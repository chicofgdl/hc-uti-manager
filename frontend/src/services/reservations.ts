import api from './api';
import { Reservation, Role } from '../types/care';

type LegacyReservation = {
  id: number;
  status: string;
  prontuario_paciente?: number | null;
  prontuario?: number | null;
  idade_paciente?: number | null;
  idade?: number | null;
  especialidade_paciente?: string | null;
  especialidade?: string | null;
  lto_lto_id?: string | null;
  criada_em?: string | null;
  atualizada_em?: string | null;
};

const normalizeStatus = (value: string): Reservation['status'] => {
  if (value === 'APROVADA' || value === 'ACEITA') return 'ACEITA';
  if (value === 'NEGADA') return 'NEGADA';
  if (value === 'CANCELADA') return 'CANCELADA';
  return 'PENDENTE';
};

const toReservation = (item: LegacyReservation, requestedBy?: Role, source: 'yaml' | 'mock-local' = 'yaml'): Reservation => {
  const prontuario = item.prontuario_paciente ?? item.prontuario ?? null;
  const especialidade = item.especialidade_paciente ?? item.especialidade ?? null;
  return {
    id: item.id,
    status: normalizeStatus(item.status),
    patient: {
      id: prontuario ? Number(prontuario) : item.id,
      external_id: prontuario ? String(prontuario) : `mock-${item.id}`,
      name: especialidade || null,
    },
    bed_code: item.lto_lto_id ?? null,
    requested_by: requestedBy,
    created_at: item.criada_em || new Date().toISOString(),
    updated_at: item.atualizada_em || new Date().toISOString(),
    prontuario_paciente: prontuario ? Number(prontuario) : null,
    idade_paciente: item.idade_paciente ?? item.idade ?? null,
    especialidade_paciente: especialidade,
    lto_lto_id: item.lto_lto_id ?? null,
    source,
  };
};

export async function listReservations(role: Role): Promise<Reservation[]> {
  if (role !== 'ICU') {
    return [];
  }
  const { data } = await api.get('/solicitacoes-reserva');
  return Array.isArray(data)
    ? data.map((item) => toReservation(item as LegacyReservation, 'SURGICAL_CENTER'))
    : [];
}

export async function listPendingReservations(): Promise<Reservation[]> {
  const { data } = await api.get('/solicitacoes-reserva/pendentes');
  return Array.isArray(data)
    ? data.map((item) => toReservation(item as LegacyReservation, 'SURGICAL_CENTER'))
    : [];
}

export async function createReservation(payload: { prontuario: string; idade: number; especialidade: string }): Promise<void> {
  await api.post('/solicitacoes-reserva', payload);
}

export async function approveReservation(reservationId: number, ltoLtoId: string): Promise<void> {
  await api.post(`/solicitacoes-reserva/${reservationId}/aprovar`, {
    lto_lto_id: ltoLtoId,
  });
}

export async function denyReservation(reservationId: number, motivo?: string): Promise<void> {
  await api.post(`/solicitacoes-reserva/${reservationId}/negar`, motivo ? { motivo } : {});
}

export async function cancelReservation(reservationId: number, motivo?: string): Promise<void> {
  await api.post(`/solicitacoes-reserva/${reservationId}/cancelar`, motivo ? { motivo } : {});
}

export function buildLocalReservation(payload: { prontuario: string; idade: number; especialidade: string }): Reservation {
  return toReservation(
    {
      id: Date.now(),
      status: 'PENDENTE',
      prontuario_paciente: Number(payload.prontuario),
      idade_paciente: payload.idade,
      especialidade_paciente: payload.especialidade,
      criada_em: new Date().toISOString(),
      atualizada_em: new Date().toISOString(),
    },
    'SURGICAL_CENTER',
    'mock-local'
  );
}
