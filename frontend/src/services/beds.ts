import api from './api';
import { Bed } from '../types/care';

type LegacyBed = {
  lto_lto_id: string;
  status?: string | null;
  alta_solicitada?: boolean;
  prontuario_atual?: number | null;
  prontuario_proximo?: number | null;
  atualizado_em?: string | null;
};

const toBed = (item: LegacyBed): Bed => {
  const hasCurrentPatient = item.prontuario_atual !== null && item.prontuario_atual !== undefined;
  const hasNextPatient = item.prontuario_proximo !== null && item.prontuario_proximo !== undefined;
  return {
    id: String(item.lto_lto_id),
    code: String(item.lto_lto_id),
    availability_status: item.alta_solicitada ? 'DISPONIVEL' : 'NAO_DISPONIVEL',
    occupancy_status: hasCurrentPatient ? 'OCUPADO' : 'LIVRE',
    legacy_status: item.status ?? null,
    alta_solicitada: Boolean(item.alta_solicitada),
    current_patient_id: hasCurrentPatient ? String(item.prontuario_atual) : null,
    next_patient_id: hasNextPatient ? String(item.prontuario_proximo) : null,
    created_at: item.atualizado_em || '',
    updated_at: item.atualizado_em || '',
  };
};

export async function fetchBeds(): Promise<Bed[]> {
  const { data } = await api.get('/leitos');
  return Array.isArray(data) ? data.map((item) => toBed(item as LegacyBed)) : [];
}

export async function fetchReservableBeds(): Promise<Bed[]> {
  const { data } = await api.get('/leitos/disponiveis-para-reserva');
  return Array.isArray(data) ? data.map((item) => toBed(item as LegacyBed)) : [];
}

export async function fetchReservableBedsCount(): Promise<number> {
  const { data } = await api.get('/leitos/quantidade-disponiveis');
  return Number(data?.quantidade_leitos_disponiveis || 0);
}

export async function updateAvailability(bedId: string, available: boolean): Promise<void> {
  if (available) {
    await api.post(`/leitos/${encodeURIComponent(bedId)}/alta`);
    return;
  }
  await api.delete(`/leitos/${encodeURIComponent(bedId)}/alta`);
}
