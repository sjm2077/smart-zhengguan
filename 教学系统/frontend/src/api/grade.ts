import api from "./index";

export interface GradeItem {
  id: number;
  student: number;
  student_name?: string;
  student_id?: string;
  course: number;
  course_name?: string;
  score: number;
  grade_point: number;
  semester: number | null;
  semester_name?: string;
  exam_type: string;
  exam_date: string;
  remark: string;
}

export interface GradeListParams {
  page?: number;
  page_size?: number;
  search?: string;
  student_id?: number;
  course_id?: number;
  semester_id?: number;
}

/** GET /api/grades/ */
export function getGrades(params?: GradeListParams): Promise<{
  count: number;
  results: GradeItem[];
}> {
  return api.get("/grades/", { params });
}

/** GET /api/grades/:id/ */
export function getGrade(id: number): Promise<GradeItem> {
  return api.get(`/grades/${id}/`);
}

/** POST /api/grades/ */
export function createGrade(data: Omit<GradeItem, "id" | "student_name" | "student_id" | "course_name" | "semester_name">): Promise<GradeItem> {
  return api.post("/grades/", data);
}

/** PUT /api/grades/:id/ */
export function updateGrade(id: number, data: Partial<Omit<GradeItem, "id" | "student_name" | "student_id" | "course_name" | "semester_name">>): Promise<GradeItem> {
  return api.put(`/grades/${id}/`, data);
}

/** DELETE /api/grades/:id/ */
export function deleteGrade(id: number): Promise<void> {
  return api.delete(`/grades/${id}/`);
}

/** GET /api/grades/statistics/ */
export function getGradeStatistics(params?: {
  semester_id?: number;
  college_id?: number;
}): Promise<{
  pass_rate: number;
  excellent_rate: number;
  avg_score: number;
  score_distribution: Record<string, number>;
}> {
  return api.get("/grades/statistics/", { params });
}