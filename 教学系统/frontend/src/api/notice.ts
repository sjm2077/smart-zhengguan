import api from "./index";

export interface NoticeItem {
  id: number;
  title: string;
  content: string;
  notice_type: "info" | "warning" | "success";
  publisher: number | null;
  publisher_name?: string;
  is_published: boolean;
  created_at: string;
  updated_at: string;
}

export interface NoticeListParams {
  page?: number;
  page_size?: number;
  notice_type?: string;
}

/** GET /api/notices/ */
export function getNotices(params?: NoticeListParams): Promise<{
  count: number;
  results: NoticeItem[];
}> {
  return api.get("/notices/", { params });
}

/** GET /api/notices/:id/ */
export function getNotice(id: number): Promise<NoticeItem> {
  return api.get(`/notices/${id}/`);
}

/** POST /api/notices/ */
export function createNotice(data: Omit<NoticeItem, "id" | "publisher_name" | "created_at" | "updated_at">): Promise<NoticeItem> {
  return api.post("/notices/", data);
}

/** PUT /api/notices/:id/ */
export function updateNotice(id: number, data: Partial<Omit<NoticeItem, "id" | "publisher_name" | "created_at" | "updated_at">>): Promise<NoticeItem> {
  return api.put(`/notices/${id}/`, data);
}

/** DELETE /api/notices/:id/ */
export function deleteNotice(id: number): Promise<void> {
  return api.delete(`/notices/${id}/`);
}