/**
 * API client for the Lead Reactivation Agent backend.
 */

import axios from "axios";

const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

// ── Leads ────────────────────────────────────────────────────────

export interface Lead {
  id: number;
  lead_id: string;
  full_name: string;
  phone_number: string;
  email?: string;
  last_interaction_date: string;
  lead_source: string;
  notes?: string;
  intent_category?: string;
  intent_rationale?: string;
  recommended_angle?: string;
  sms_tone?: string;
  state: string;
  batch_id?: string;
  created_at?: string;
  updated_at?: string;
}

export interface LeadListResponse {
  leads: Lead[];
  total: number;
  page: number;
  page_size: number;
}

export interface LeadFilters {
  page?: number;
  page_size?: number;
  state?: string;
  intent?: string;
  source?: string;
  batch_id?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
}

export const fetchLeads = (filters: LeadFilters = {}) =>
  api.get<LeadListResponse>("/leads/", { params: filters }).then((r) => r.data);

export const fetchLead = (leadId: string) =>
  api.get<Lead>(`/leads/${leadId}`).then((r) => r.data);

export const fetchLeadMessages = (leadId: string) =>
  api.get(`/leads/${leadId}/messages`).then((r) => r.data);

// ── Batches ──────────────────────────────────────────────────────

export interface Batch {
  id: number;
  batch_id: string;
  filename?: string;
  total_leads: number;
  processed_leads: number;
  status: string;
  created_at?: string;
  completed_at?: string;
}

export const uploadCSV = (file: File) => {
  const form = new FormData();
  form.append("file", file);
  return api
    .post<Batch>("/leads/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    .then((r) => r.data);
};

export const processBatch = (batchId: string) =>
  api.post(`/leads/process/${batchId}`).then((r) => r.data);

export const fetchBatches = () =>
  api.get<Batch[]>("/leads/batches/list").then((r) => r.data);

// ── Dashboard ────────────────────────────────────────────────────

export interface DashboardKPIs {
  total_leads: number;
  total_messages_sent: number;
  total_replies: number;
  total_ignored: number;
  total_opted_out: number;
  reply_rate: number;
  ignored_rate: number;
  avg_reply_time_minutes?: number;
}

export interface IntentBreakdown {
  intent_category: string;
  count: number;
  reply_count: number;
  reply_rate: number;
}

export interface DashboardData {
  kpis: DashboardKPIs;
  intent_breakdown: IntentBreakdown[];
  state_distribution: Record<string, number>;
  source_distribution: Record<string, number>;
  daily_messages: Array<{ date: string; count: number }>;
}

export const fetchDashboard = () =>
  api.get<DashboardData>("/dashboard/").then((r) => r.data);

// ── Config ───────────────────────────────────────────────────────

export interface AppConfig {
  business_hours_start: string;
  business_hours_end: string;
  business_hours_timezone: string;
  default_sms_tone: string;
  ignore_timeout_hours: number;
  max_retries: number;
}

export const fetchConfig = () =>
  api.get<AppConfig>("/config/").then((r) => r.data);

export const updateConfig = (payload: Partial<AppConfig>) =>
  api.put<AppConfig>("/config/", payload).then((r) => r.data);

// ── Export ────────────────────────────────────────────────────────

export const exportCSV = (filters: Partial<LeadFilters> = {}) => {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => {
    if (v) params.set(k, String(v));
  });
  window.open(`/api/v1/leads/export/csv?${params.toString()}`, "_blank");
};

export default api;
