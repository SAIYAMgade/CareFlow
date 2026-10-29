export interface Patient {
  patient_id: number;
  mrn: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  phone?: string;
  email?: string;
  address?: string;
  status: 'ACTIVE' | 'INACTIVE' | 'MERGED';
  created_at: string;
  updated_at: string;
}

export interface PatientListResponse {
  items: Patient[];
  total: number;
  page: number;
  page_size: number;
}

export interface Appointment {
  appointment_id: number;
  patient_id: number;
  appointment_time: string;
  appointment_type: string;
  department: string;
  provider_name: string;
  status: 'SCHEDULED' | 'CHECKED_IN' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED' | 'NO_SHOW';
  check_in_time?: string;
  cancel_reason?: string;
  patient_name?: string;
  patient_mrn?: string;
  created_at: string;
  updated_at: string;
}

export interface AppointmentListResponse {
  items: Appointment[];
  total: number;
  page: number;
  page_size: number;
}

export interface Encounter {
  encounter_id: number;
  patient_id: number;
  appointment_id?: number;
  encounter_type: string;
  department: string;
  provider_name: string;
  status: 'OPEN' | 'IN_PROGRESS' | 'AWAITING_RESULTS' | 'COMPLETED' | 'CANCELLED';
  start_time: string;
  end_time?: string;
  chief_complaint?: string;
  clinical_notes?: string;
  patient_name?: string;
  patient_mrn?: string;
  created_at: string;
  updated_at: string;
}

export interface EncounterListResponse {
  items: Encounter[];
  total: number;
  page: number;
  page_size: number;
}

export interface Observation {
  observation_id: number;
  encounter_id: number;
  patient_id: number;
  observation_type: string;
  observation_code: string;
  value_numeric?: number;
  value_text?: string;
  unit?: string;
  observation_time: string;
  status: string;
  source: string;
}

export interface Order {
  order_id: number;
  encounter_id: number;
  patient_id: number;
  order_type: string;
  order_code: string;
  order_name: string;
  order_status: 'ORDERED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
  priority: 'STAT' | 'URGENT' | 'ROUTINE';
  ordered_by: string;
  ordered_at: string;
  completed_at?: string;
  patient_name?: string;
  patient_mrn?: string;
  department?: string;
}

export interface OrderListResponse {
  items: Order[];
  total: number;
  page: number;
  page_size: number;
}

export interface Result {
  result_id: number;
  order_id: number;
  result_value: string;
  reference_range?: string;
  unit?: string;
  abnormal_flag: 'NORMAL' | 'HIGH' | 'LOW' | 'CRITICAL';
  result_status: 'PENDING_REVIEW' | 'REVIEWED' | 'AMENDED';
  reviewed_by?: string;
  reviewed_at?: string;
  result_time: string;
  order_name?: string;
  order_code?: string;
  patient_name?: string;
  patient_mrn?: string;
  department?: string;
}

export interface ResultListResponse {
  items: Result[];
  total: number;
  page: number;
  page_size: number;
}

export interface ReportParameter {
  name: string;
  label: string;
  type: string;
  default?: string;
  options?: string[];
}

export interface ReportCatalogItem {
  id: string;
  title: string;
  category: string;
  description: string;
  business_question: string;
  parameters: ReportParameter[];
}

export interface ReportExecutionResult {
  report_id: string;
  title: string;
  columns: string[];
  rows: Record<string, any>[];
  total_rows: number;
  page: number;
  page_size: number;
  executed_at: string;
  execution_time_ms: number;
  dialect: string;
}

export interface DataQualityIssue {
  issue_id: number;
  rule_code: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  affected_entity: string;
  entity_id: number;
  detection_time: string;
  description: string;
  investigation_steps: string;
  resolution_status: 'OPEN' | 'INVESTIGATING' | 'RESOLVED' | 'FALSE_POSITIVE';
  resolved_by?: string;
  resolved_at?: string;
  remediation_notes?: string;
}

export interface AuditLog {
  audit_id: number;
  entity_type: string;
  entity_id: number;
  action: string;
  actor: string;
  previous_state?: string;
  new_state?: string;
  correlation_id?: string;
  reason?: string;
  changed_at: string;
}

export interface DashboardKpis {
  appointments_today: number;
  patients_checked_in: number;
  patients_waiting: number;
  encounters_in_progress: number;
  encounters_completed_today: number;
  orders_awaiting_results: number;
  results_awaiting_review: number;
  open_data_quality_issues: number;
}

export interface DashboardChartsResponse {
  hourly_volume: Array<{ hour: number; scheduled: number; checked_in: number }>;
  encounter_distribution: Array<{ status: string; count: number }>;
  wait_time_by_dept: Array<{ department: string; avg_wait_minutes: number }>;
  order_turnaround: Array<{ order_code: string; order_name: string; avg_turnaround_hours: number }>;
  exceptions_by_severity: Array<{ severity: string; count: number }>;
}

export interface SystemHealth {
  status: string;
  application: string;
  version: string;
  environment: string;
  database: {
    status: string;
    dialect: string;
    database_version?: string;
    server_time?: string;
    connected: boolean;
    error?: string;
  };
}
