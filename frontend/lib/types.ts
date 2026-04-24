export type UserRole = "director" | "delegate";

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export type EquipmentCategory =
  | "laptop"
  | "desktop"
  | "printer"
  | "phone"
  | "tablet"
  | "monitor"
  | "projector"
  | "other";

export type EquipmentStatus = "active" | "retired";

export interface Equipment {
  id: string;
  name: string;
  category: EquipmentCategory;
  manufacturer?: string;
  model?: string;
  serial_number?: string;
  qr_code: string;
  location_id: string;
  room?: string;
  assigned_to?: string;
  status: EquipmentStatus;
  retired_at?: string;
  retired_by_id?: string;
  retirement_reason?: string;
  created_at: string;
  updated_at: string;
  created_by_id: string;
}

export interface EquipmentListResponse {
  items: Equipment[];
  total: number;
}

export interface Location {
  id: string;
  name: string;
  address?: string;
  created_at: string;
  updated_at: string;
}

export interface LocationListResponse {
  items: Location[];
  total: number;
}

export type AuditSessionStatus = "in_progress" | "completed";
export type CheckMethod = "scan" | "manual";

export interface AuditSession {
  id: string;
  location_id: string;
  started_by_id: string;
  started_at: string;
  completed_at?: string;
  status: AuditSessionStatus;
  notes?: string;
}

export interface AuditItem {
  id: string;
  audit_session_id: string;
  equipment_id: string;
  check_method?: CheckMethod;
  checked_at?: string;
  is_present?: boolean;
  equipment?: Equipment;
}

export interface AuditSummary {
  total: number;
  present: number;
  missing: number;
  unchecked: number;
}

export interface AuditDetail {
  session: AuditSession;
  summary: AuditSummary;
  items: AuditItem[];
}

export interface AuditListResponse {
  items: AuditSession[];
  total: number;
}

export interface AuditReport {
  session: AuditSession;
  location_id: string;
  auditor_id: string;
  auditor_name: string;
  summary: AuditSummary;
  present_items: Equipment[];
  missing_items: Equipment[];
  unchecked_items: Equipment[];
}

export interface UserListResponse {
  items: AuthUser[];
  total: number;
}
