import api from "./index";

export interface KpiSummary {
  total_students: number;
  total_courses: number;
  avg_score: number;
  exam_pass_rate: number;
}

/** GET /api/dashboard/summary/ */
export function getDashboardSummary(params?: {
  semester_id?: number;
  college_id?: number;
}): Promise<KpiSummary> {
  return api.get("/dashboard/summary/", { params });
}

// ----------------------------------------------------------------
// Semester / College 基础数据 (用于筛选器)
// ----------------------------------------------------------------
export interface SemesterItem {
  id: number;
  name: string;
}

export interface CollegeItem {
  id: number;
  name: string;
}

export function getSemesters(): Promise<SemesterItem[]> {
  return api.get("/dashboard/semesters/");
}

export function getColleges(): Promise<CollegeItem[]> {
  return api.get("/dashboard/colleges/");
}

export interface GraduateEmploymentItem {
  name: string;
  value: number;
}

export interface GraduateEmploymentResponse {
  year: number | null;
  total: number;
  data: GraduateEmploymentItem[];
}

export interface DashboardAlertItem {
  id: string;
  level: "red" | "orange" | "yellow";
  levelLabel: string;
  title: string;
  desc: string;
}

export interface DashboardLiveItem {
  id: number;
  time: string;
  text: string;
  module?: string;
  action?: string;
  actor?: string;
}

/** GET /api/dashboard/graduate-employment/ */
export function getGraduateEmploymentStats(params?: {
  year?: number;
  college_id?: number;
}): Promise<GraduateEmploymentResponse> {
  return api.get("/dashboard/graduate-employment/", { params }) as unknown as Promise<GraduateEmploymentResponse>;
}

export interface SaveGraduateEmploymentPayload {
  year: number;
  college_id: number;
  destination_type:
    | 'employment'
    | 'further_study'
    | 'civil_service'
    | 'flexible'
    | 'entrepreneurship'
    | 'unemployed'
    | 'other';
  count: number;
}

export interface SaveGraduateEmploymentResult {
  id: number;
  year: number;
  college_id: number;
  destination_type: string;
  destination_label: string;
  count: number;
}

/** POST /api/dashboard/graduate-employment/ */
export function saveGraduateEmploymentStat(
  payload: SaveGraduateEmploymentPayload,
): Promise<SaveGraduateEmploymentResult> {
  return api.post(
    '/dashboard/graduate-employment/',
    payload,
  ) as unknown as Promise<SaveGraduateEmploymentResult>;
}


/** GET /api/dashboard/alerts/ */
export function getDashboardAlerts(): Promise<{ results: DashboardAlertItem[] }> {
  return api.get("/dashboard/alerts/") as unknown as Promise<{ results: DashboardAlertItem[] }>;
}

/** GET /api/dashboard/live-feed/ */
export function getDashboardLiveFeed(params?: { limit?: number }): Promise<{ results: DashboardLiveItem[] }> {
  return api.get("/dashboard/live-feed/", { params }) as unknown as Promise<{ results: DashboardLiveItem[] }>;
}
