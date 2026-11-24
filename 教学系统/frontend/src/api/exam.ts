import api from "./index";

export interface ExamItem {
  id: number;
  name: string;
  course: number;
  course_name?: string;
  course_code?: string;
  semester: number;
  semester_name?: string;
  exam_type: string;
  exam_date: string;         // ISO datetime
  duration: number;           // 分钟
  total_score: number;
  location: string;
}

export interface ExamListParams {
  page?: number;
  page_size?: number;
  search?: string;
  course_id?: number;
  semester_id?: number;
}

/** GET /api/exams/ */
export function getExams(params?: ExamListParams): Promise<{
  count: number;
  results: ExamItem[];
}> {
  return api.get("/exams/", { params });
}

/** GET /api/exams/:id/ */
export function getExam(id: number): Promise<ExamItem> {
  return api.get(`/exams/${id}/`);
}

/** POST /api/exams/ */
export function createExam(data: Omit<ExamItem, "id" | "course_name" | "course_code" | "semester_name">): Promise<ExamItem> {
  return api.post("/exams/", data);
}

/** PUT /api/exams/:id/ */
export function updateExam(id: number, data: Partial<Omit<ExamItem, "id" | "course_name" | "course_code" | "semester_name">>): Promise<ExamItem> {
  return api.put(`/exams/${id}/`, data);
}

/** DELETE /api/exams/:id/ */
export function deleteExam(id: number): Promise<void> {
  return api.delete(`/exams/${id}/`);
}