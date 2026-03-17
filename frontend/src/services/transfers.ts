import api from './api';
import { Transfer, Role } from '../types/care';

export async function listTransfers(role: Role): Promise<Transfer[]> {
  const endpoint =
    role === 'SURGICAL_CENTER'
      ? '/api/surgical-center/transfers'
      : '/api/icu/transfers';
  const { data } = await api.get(endpoint);
  return data;
}

export async function listTransfersCc(): Promise<Transfer[]> {
  const { data } = await api.get('/api/surgical-center/transfers');
  return data;
}

export async function createTransfer(payload: { patientId: string; reservationId?: number | null; bedId?: number | null; notes?: string | null }): Promise<Transfer> {
  const { data } = await api.post('/api/surgical-center/transfers', payload);
  return data;
}

export async function decideTransfer(transferId: number, decision: 'ACCEPT' | 'DENY', bedId?: number | null): Promise<Transfer> {
  const { data } = await api.patch(`/api/icu/transfers/${transferId}/decision`, {
    decision,
    bedId: bedId || null,
  });
  return data;
}
