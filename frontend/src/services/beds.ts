import api from './api';
import { Bed } from '../types/care';

export async function fetchBeds(): Promise<Bed[]> {
  const { data } = await api.get('/api/icu/beds');
  return data;
}

export async function fetchAvailableCount(): Promise<number> {
  const { data } = await api.get('/api/icu/beds/available-count');
  return data.count;
}

export async function updateAvailability(bedId: number, available: boolean): Promise<Bed> {
  const { data } = await api.patch(`/api/icu/beds/${bedId}/availability`, {
    availableForReservation: available,
  });
  return data;
}
