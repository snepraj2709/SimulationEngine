import { ApiErrorPayload } from "@/types/api";
import { useAuthStore } from "@/store/auth-store";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  code: string;
  requestId?: string;

  constructor(message: string, code: string, requestId?: string) {
    super(message);
    this.code = code;
    this.requestId = requestId;
  }
}

interface RequestOptions extends RequestInit {
  auth?: boolean;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { token } = useAuthStore.getState();
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (options.auth !== false && token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorPayload = (await response.json().catch(() => null)) as ApiErrorPayload | null;
    if (errorPayload?.error) {
      throw new ApiError(
        errorPayload.error.message,
        errorPayload.error.code,
        errorPayload.error.request_id,
      );
    }
    throw new ApiError("Request failed.", "request_failed");
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
