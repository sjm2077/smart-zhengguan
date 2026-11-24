
/**
 * API 服务层 — 统一封装 axios + JWT 认证
 *
 * 功能：
 *  - 自动附带 Authorization header
 *  - Token 过期自动刷新
 *  - 并发请求共享同一次 Token 刷新
 *  - 统一处理认证失败
 *  - 请求/响应拦截
 */

import axios, {
  type AxiosInstance,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from "axios";

// ----------------------------------------------------------------
// Token 管理
// ----------------------------------------------------------------

const TOKEN_KEY = "teaching_system_access_token";
const REFRESH_KEY = "teaching_system_refresh_token";

export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setTokens(access: string, refresh: string): void {
  localStorage.setItem(TOKEN_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

// ----------------------------------------------------------------
// Axios 请求类型
// ----------------------------------------------------------------

type RetryableRequestConfig = InternalAxiosRequestConfig & {
  _retry?: boolean;
};

interface RefreshResponse {
  access: string;
  refresh?: string;
}

// ----------------------------------------------------------------
// 创建 Axios 实例
// ----------------------------------------------------------------

const api: AxiosInstance = axios.create({
  baseURL: "/api",
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});

// ----------------------------------------------------------------
// 请求拦截器 — 自动附带 Token
// ----------------------------------------------------------------

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAccessToken();
    const url = config.url ?? "";

    // 登录请求不应携带旧的访问令牌
    const isLoginRequest = url.includes("/auth/login/");
    const isRefreshRequest = url.includes("/auth/refresh/");

    if (
      token &&
      !isLoginRequest &&
      !isRefreshRequest &&
      config.headers
    ) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error: unknown) => Promise.reject(error),
);

// ----------------------------------------------------------------
// 响应拦截器 — Token 刷新与错误处理
// ----------------------------------------------------------------

// 多个请求同时遇到 401 时，共享同一个刷新 Promise
let refreshPromise: Promise<string> | null = null;

api.interceptors.response.use(
  (response: AxiosResponse) => response.data,

  async (error: unknown) => {
    const axiosError = error as {
      config?: RetryableRequestConfig;
      response?: {
        status?: number;
      };
    };

    const originalRequest = axiosError.config;
    const requestUrl = originalRequest?.url ?? "";

    const isLoginRequest = requestUrl.includes("/auth/login/");
    const isRefreshRequest = requestUrl.includes("/auth/refresh/");

    // 只处理需要刷新的 401 请求
    if (
      axiosError.response?.status !== 401 ||
      !originalRequest ||
      originalRequest._retry ||
      isLoginRequest ||
      isRefreshRequest
    ) {
      return Promise.reject(error);
    }

    // 标记原请求，防止刷新后再次无限重试
    originalRequest._retry = true;

    // 如果没有正在进行的刷新，则创建一次刷新任务
    if (!refreshPromise) {
      const refreshToken = localStorage.getItem(REFRESH_KEY);

      if (!refreshToken) {
        clearTokens();
        window.location.href = "/login";
        return Promise.reject(error);
      }

      refreshPromise = axios
        .post<RefreshResponse>("/api/auth/refresh/", {
          refresh: refreshToken,
        })
        .then((response) => {
          const newAccess = response.data?.access;

          if (!newAccess) {
            throw new Error("Token 刷新接口未返回有效的 access 字段");
          }

          // 兼容后端轮换 refresh Token 的情况
          setTokens(
            newAccess,
            response.data.refresh ?? refreshToken,
          );

          return newAccess;
        })
        .catch((refreshError: unknown) => {
          clearTokens();
          window.location.href = "/login";

          throw refreshError;
        })
        .finally(() => {
          refreshPromise = null;
        });
    }

    // 所有等待中的请求使用同一个刷新结果
    const pendingRefresh = refreshPromise;

    if (!pendingRefresh) {
      return Promise.reject(error);
    }

    try {
      const newAccess = await pendingRefresh;

      originalRequest.headers.Authorization = `Bearer ${newAccess}`;

      // 使用新的访问令牌重放原请求
      return api(originalRequest);
    } catch (refreshError) {
      return Promise.reject(refreshError);
    }
  },
);

export default api;

// ----------------------------------------------------------------
// 各模块 API 统一导出
// ----------------------------------------------------------------

export * from "./auth";
export * from "./dashboard";
export * from "./student";
export * from "./course";
export * from "./exam";
export * from "./grade";
export * from "./analysis";
export * from "./teacher";
export * from "./notice";
