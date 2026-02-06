import api from './api';
import { Notification, Role } from '../types/care';

export async function fetchNotifications(role: Role, unreadOnly = false): Promise<Notification[]> {
  const { data } = await api.get('/api/notifications', {
    params: { role, unreadOnly },
  });
  return data;
}

export async function markNotificationRead(id: number): Promise<Notification> {
  const { data } = await api.patch(`/api/notifications/${id}/read`);
  return data;
}

export async function markAllRead(role: Role): Promise<void> {
  await api.patch('/api/notifications/read-all', null, { params: { role } });
}
