import api from "./index";

export interface StudentItem {
  id: number;
  student_no: string;       // 学号 (backend field)
  name: string;
  gender: string;
  college: number;
  college_name?: string;
  major: string;
  grade: string;
  class_name: string;
  email: string;
  phone: string;
  enrollment_year: number;
}

export interface StudentListParams {
  page?: number;
  page_size?: number;
  search?: string;
  college_id?: number;
  grade?: string;
}

/** GET /api/students/ */
export function getStudents(params?: StudentListParams): Promise<{
  count: number;
  results: StudentItem[];
}> {
  return api.get("/students/", { params });
}

/** GET /api/students/:id/ */
export function getStudent(id: number): Promise<StudentItem> {
  return api.get(`/students/${id}/`);
}

/** POST /api/students/ */
export function createStudent(data: Omit<StudentItem, "id" | "college_name">): Promise<StudentItem> {
  return api.post("/students/", data);
}

/** PUT /api/students/:id/ */
export function updateStudent(id: number, data: Partial<Omit<StudentItem, "id" | "college_name">>): Promise<StudentItem> {
  return api.put(`/students/${id}/`, data);
}

/** DELETE /api/students/:id/ */
export function deleteStudent(id: number): Promise<void> {
  return api.delete(`/students/${id}/`);
}