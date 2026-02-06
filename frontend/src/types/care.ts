export type Role = 'ICU' | 'SURGICAL_CENTER';

export type BedAvailability = 'NAO_DISPONIVEL' | 'DISPONIVEL';
export type BedOccupancy = 'LIVRE' | 'OCUPADO';

export interface Bed {
  id: number;
  code: string;
  availability_status: BedAvailability;
  occupancy_status: BedOccupancy;
  created_at: string;
  updated_at: string;
}

export interface Patient {
  id: number;
  external_id: string;
  name?: string | null;
  location?: string | null;
  current_bed_id?: number | null;
}

export type ReservationStatus = 'PENDENTE' | 'ACEITA' | 'NEGADA' | 'CANCELADA';

export interface Reservation {
  id: number;
  status: ReservationStatus;
  patient: Patient;
  notes?: string | null;
  preferred_datetime?: string | null;
  bed_id?: number | null;
  requested_by: Role;
  cancellation_reason?: string | null;
  created_at: string;
  updated_at: string;
  decided_at?: string | null;
}

export type TransferStatus = 'PENDENTE' | 'ACEITA' | 'NEGADA' | 'CANCELADA';

export interface Transfer {
  id: number;
  status: TransferStatus;
  patient: Patient;
  reservation_id?: number | null;
  bed_id?: number | null;
  requested_by: Role;
  created_at: string;
  updated_at: string;
  decided_at?: string | null;
}

export type NotificationType =
  | 'RESERVA_CRIADA'
  | 'RESERVA_ATUALIZADA'
  | 'TRANSFERENCIA_CRIADA'
  | 'TRANSFERENCIA_ATUALIZADA';

export interface Notification {
  id: number;
  type: NotificationType;
  message: string;
  reference_type?: string | null;
  reference_id?: number | null;
  recipient_role: Role;
  read: boolean;
  created_at: string;
  updated_at: string;
}
