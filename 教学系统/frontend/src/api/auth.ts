import api from "./index";

export interface LoginParams {
  username: string;
  password: string;
}

export interface LoginResult {
  token: string;
  refresh: string;
  user: UserInfo;
}

/** POST /api/auth/login/ */
export function login(params: LoginParams): Promise<LoginResult> {
  return api.post("/auth/login/", params);
}

export interface UserInfo {
  id: number;
  username: string;
  role: string;
  avatar: string | null;
}

/** GET /api/auth/me/ */
export function getMe(): Promise<UserInfo> {
  return api.get("/auth/me/");
}

/** POST /api/auth/refresh/ */
export function refreshToken(refresh: string): Promise<{ access: string }> {
  return api.post("/auth/refresh/", { refresh });
}
