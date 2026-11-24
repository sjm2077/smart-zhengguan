import api from "./index";

export interface TeacherItem {
  id: number;
  teacher_no: string;
  name: string;
  gender: string;
  college: number;
  college_name?: string;
  title: string;
  phone: string;
  email: string;
  description: string;
}


export interface TeacherListParams {
  page?: number;
  page_size?: number;
  search?: string;
  college_id?: number;
  is_active?: boolean;
}


/** GET /api/teachers/ */
export function getTeachers(params?: TeacherListParams): Promise<{
  count: number;
  results: TeacherItem[];
}> {
  return api.get("/teachers/", { params });
}

/** GET /api/teachers/:id/ */
export function getTeacher(id: number): Promise<TeacherItem> {
  return api.get(`/teachers/${id}/`);
}

/** POST /api/teachers/ */
export function createTeacher(data: Omit<TeacherItem, "id" | "college_name">): Promise<TeacherItem> {
  return api.post("/teachers/", data);
}

/** PUT /api/teachers/:id/ */
export function updateTeacher(id: number, data: Partial<Omit<TeacherItem, "id" | "college_name">>): Promise<TeacherItem> {
  return api.put(`/teachers/${id}/`, data);
}

/** DELETE /api/teachers/:id/ */
export function deleteTeacher(id: number): Promise<void> {
  return api.delete(`/teachers/${id}/`);
}