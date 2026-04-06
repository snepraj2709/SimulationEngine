import { apiRequest } from "@/api/client";
import { TokenResponse, User } from "@/types/api";

export function registerUser(payload: { email: string; password: string; full_name: string }) {
  return apiRequest<TokenResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
    auth: false,
  });
}

export function loginUser(payload: { email: string; password: string }) {
  return apiRequest<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
    auth: false,
  });
}

export function getCurrentUser() {
  return apiRequest<User>("/auth/me");
}
