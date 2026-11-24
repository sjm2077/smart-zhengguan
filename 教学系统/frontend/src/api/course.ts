import api from "./index";

export interface CourseItem {
  id: number;
  code: string;
  name: string;
  credit: number;
  hours: number;
  college: number;
  college_name?: string;
  semester: number | null;
  semester_name?: string;
  course_type: string;
  description: string;
}

export interface CourseListParams {
  page?: number;
  page_size?: number;
  search?: string;
  college_id?: number;
  type?: string;
  is_active?: boolean;
}

/** GET /api/courses/ */
export function getCourses(params?: CourseListParams): Promise<{
  count: number;
  results: CourseItem[];
}> {
  return api.get("/courses/", { params });
}

/** GET /api/courses/:id/ */
export function getCourse(id: number): Promise<CourseItem> {
  return api.get(`/courses/${id}/`);
}

/** POST /api/courses/ */
export function createCourse(data: Omit<CourseItem, "id" | "college_name" | "semester_name">): Promise<CourseItem> {
  return api.post("/courses/", data);
}

/** PUT /api/courses/:id/ */
export function updateCourse(id: number, data: Partial<Omit<CourseItem, "id" | "college_name" | "semester_name">>): Promise<CourseItem> {
  return api.put(`/courses/${id}/`, data);
}

/** DELETE /api/courses/:id/ */
export function deleteCourse(id: number): Promise<void> {
  return api.delete(`/courses/${id}/`);
}