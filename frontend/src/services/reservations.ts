import api from './api';
import { Reservation, Role } from '../types/care';

export async function listReservations(role: Role): Promise<Reservation[]> {
  const endpoint =
    role === 'SURGICAL_CENTER'
      ? '/api/surgical-center/reservations'
      : '/api/icu/reservations';
  const { data } = await api.get(endpoint);
  return data;
}

export async function listReservationsCc(): Promise<Reservation[]> {
  const { data } = await api.get('/api/surgical-center/reservations');
  return data;
}

export async function createReservation(payload: { patientId: string; notes?: string; preferredDateTime?: string | null }): Promise<Reservation> {
  const { data } = await api.post('/api/surgical-center/reservations', payload);
  return data;
}

export async function decideReservation(reservationId: number, decision: 'ACCEPT' | 'DENY', bedId?: number | null): Promise<Reservation> {
  const { data } = await api.patch(`/api/icu/reservations/${reservationId}/decision`, {
    decision,
    bedId: bedId || null,
  });
  return data;
}

export async function cancelReservationCc(reservationId: number, reason?: string): Promise<Reservation> {
  const { data } = await api.patch(`/api/surgical-center/reservations/${reservationId}/cancel`, {
    reason,
  });
  return data;
}

export async function cancelReservationIcu(reservationId: number, reason?: string): Promise<Reservation> {
  const { data } = await api.patch(`/api/icu/reservations/${reservationId}/cancel`, {
    reason,
  });
  return data;
}
