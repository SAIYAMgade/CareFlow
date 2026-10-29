import {
  Patient, PatientListResponse,
  Appointment, AppointmentListResponse,
  Encounter, EncounterListResponse,
  Observation,
  Order, OrderListResponse,
  Result, ResultListResponse,
  ReportCatalogItem, ReportExecutionResult,
  DataQualityIssue,
  AuditLog,
  DashboardKpis, DashboardChartsResponse,
  SystemHealth
} from '../types';

const API_BASE = '/api';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    let errorMsg = `HTTP Error ${response.status}`;
    try {
      const errJson = await response.json();
      errorMsg = errJson.message || errJson.detail || errorMsg;
    } catch {
      // ignore
    }
    throw new Error(errorMsg);
  }
  return response.json();
}

export const api = {
  // Dashboard
  getStats: () => request<DashboardKpis>('/dashboard/stats'),
  getCharts: () => request<DashboardChartsResponse>('/dashboard/charts'),

  // Patients
  getPatients: (params?: { search?: string; status?: string; page?: number; page_size?: number }) => {
    const q = new URLSearchParams();
    if (params?.search) q.append('search', params.search);
    if (params?.status) q.append('status', params.status);
    if (params?.page) q.append('page', params.page.toString());
    if (params?.page_size) q.append('page_size', params.page_size.toString());
    return request<PatientListResponse>(`/patients?${q.toString()}`);
  },
  getPatient: (id: number) => request<Patient>(`/patients/${id}`),
  createPatient: (data: Partial<Patient>) => request<Patient>('/patients', {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  updatePatient: (id: number, data: Partial<Patient>) => request<Patient>(`/patients/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data)
  }),

  // Appointments
  getAppointments: (params?: { date?: string; department?: string; status?: string; patient_id?: number; page?: number; page_size?: number }) => {
    const q = new URLSearchParams();
    if (params?.date) q.append('date', params.date);
    if (params?.department) q.append('department', params.department);
    if (params?.status) q.append('status', params.status);
    if (params?.patient_id) q.append('patient_id', params.patient_id.toString());
    if (params?.page) q.append('page', params.page.toString());
    if (params?.page_size) q.append('page_size', params.page_size.toString());
    return request<AppointmentListResponse>(`/appointments?${q.toString()}`);
  },
  getAppointment: (id: number) => request<Appointment>(`/appointments/${id}`),
  createAppointment: (data: any) => request<Appointment>('/appointments', {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  checkInAppointment: (id: number, actor: string = 'FRONT_DESK') => request<any>(`/appointments/${id}/check-in`, {
    method: 'POST',
    body: JSON.stringify({ actor })
  }),
  cancelAppointment: (id: number, cancel_reason: string, actor: string = 'CLINIC_STAFF') => request<Appointment>(`/appointments/${id}/cancel`, {
    method: 'POST',
    body: JSON.stringify({ cancel_reason, actor })
  }),
  rescheduleAppointment: (id: number, new_appointment_time: string, actor: string = 'CLINIC_STAFF') => request<Appointment>(`/appointments/${id}/reschedule`, {
    method: 'POST',
    body: JSON.stringify({ new_appointment_time, actor })
  }),

  // Encounters
  getEncounters: (params?: { patient_id?: number; department?: string; status?: string; page?: number; page_size?: number }) => {
    const q = new URLSearchParams();
    if (params?.patient_id) q.append('patient_id', params.patient_id.toString());
    if (params?.department) q.append('department', params.department);
    if (params?.status) q.append('status', params.status);
    if (params?.page) q.append('page', params.page.toString());
    if (params?.page_size) q.append('page_size', params.page_size.toString());
    return request<EncounterListResponse>(`/encounters?${q.toString()}`);
  },
  getEncounter: (id: number) => request<Encounter>(`/encounters/${id}`),
  createEncounter: (data: any) => request<Encounter>('/encounters', {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  updateEncounterStatus: (id: number, new_status: string, actor: string = 'PHYSICIAN', clinical_notes?: string) => request<Encounter>(`/encounters/${id}/status`, {
    method: 'PUT',
    body: JSON.stringify({ new_status, actor, clinical_notes })
  }),
  updateEncounterNotes: (id: number, clinical_notes: string, actor: string = 'PHYSICIAN') => request<Encounter>(`/encounters/${id}/notes`, {
    method: 'PUT',
    body: JSON.stringify({ clinical_notes, actor })
  }),

  // Observations
  getObservations: (params: { encounter_id?: number; patient_id?: number }) => {
    const q = new URLSearchParams();
    if (params.encounter_id) q.append('encounter_id', params.encounter_id.toString());
    if (params.patient_id) q.append('patient_id', params.patient_id.toString());
    return request<Observation[]>(`/observations?${q.toString()}`);
  },
  createObservation: (data: any) => request<Observation>('/observations', {
    method: 'POST',
    body: JSON.stringify(data)
  }),

  // Orders & Results
  getOrders: (params?: { encounter_id?: number; patient_id?: number; status?: string; priority?: string; page?: number; page_size?: number }) => {
    const q = new URLSearchParams();
    if (params?.encounter_id) q.append('encounter_id', params.encounter_id.toString());
    if (params?.patient_id) q.append('patient_id', params.patient_id.toString());
    if (params?.status) q.append('status', params.status);
    if (params?.priority) q.append('priority', params.priority);
    if (params?.page) q.append('page', params.page.toString());
    if (params?.page_size) q.append('page_size', params.page_size.toString());
    return request<OrderListResponse>(`/orders?${q.toString()}`);
  },
  createOrder: (data: any) => request<Order>('/orders', {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  completeOrder: (id: number, data: any) => request<Result>(`/orders/${id}/complete`, {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  getResults: (params?: { result_status?: string; abnormal_only?: boolean; page?: number; page_size?: number }) => {
    const q = new URLSearchParams();
    if (params?.result_status) q.append('result_status', params.result_status);
    if (params?.abnormal_only) q.append('abnormal_only', 'true');
    if (params?.page) q.append('page', params.page.toString());
    if (params?.page_size) q.append('page_size', params.page_size.toString());
    return request<ResultListResponse>(`/results?${q.toString()}`);
  },
  reviewResult: (id: number, reviewer: string) => request<Result>(`/results/${id}/review`, {
    method: 'POST',
    body: JSON.stringify({ reviewer })
  }),

  // Reports
  getReportCatalog: () => request<ReportCatalogItem[]>('/reports/catalog'),
  executeReport: (report_id: string, parameters: Record<string, any> = {}, page: number = 1, page_size: number = 25) => request<ReportExecutionResult>('/reports/execute', {
    method: 'POST',
    body: JSON.stringify({ report_id, parameters, page, page_size })
  }),
  exportReportCsvUrl: (report_id: string, parameters: Record<string, any> = {}) => {
    // Return fetch blob downloader
    return async () => {
      const res = await fetch(`${API_BASE}/reports/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ report_id, parameters })
      });
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${report_id.toLowerCase()}_export.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    };
  },

  // Data Quality
  getDataQualityIssues: (params?: { status?: string; severity?: string; entity?: string; page?: number; page_size?: number }) => {
    const q = new URLSearchParams();
    if (params?.status) q.append('status', params.status);
    if (params?.severity) q.append('severity', params.severity);
    if (params?.entity) q.append('entity', params.entity);
    if (params?.page) q.append('page', params.page.toString());
    if (params?.page_size) q.append('page_size', params.page_size.toString());
    return request<{ items: DataQualityIssue[]; total: number; page: number; page_size: number }>(`/data-quality/issues?${q.toString()}`);
  },
  runDataQualityScan: () => request<any>('/data-quality/scan', { method: 'POST' }),
  resolveDataQualityIssue: (id: number, resolved_by: string, remediation_notes: string, resolution_status: string = 'RESOLVED') => request<DataQualityIssue>(`/data-quality/issues/${id}/resolve`, {
    method: 'POST',
    body: JSON.stringify({ resolved_by, remediation_notes, resolution_status })
  }),

  // Audit
  getAuditLogs: (params?: { entity_type?: string; entity_id?: number; actor?: string; page?: number; page_size?: number }) => {
    const q = new URLSearchParams();
    if (params?.entity_type) q.append('entity_type', params.entity_type);
    if (params?.entity_id) q.append('entity_id', params.entity_id.toString());
    if (params?.actor) q.append('actor', params.actor);
    if (params?.page) q.append('page', params.page.toString());
    if (params?.page_size) q.append('page_size', params.page_size.toString());
    return request<{ items: AuditLog[]; total: number; page: number; page_size: number }>(`/audit?${q.toString()}`);
  },

  // Health
  getSystemHealth: () => request<SystemHealth>('/health')
};
