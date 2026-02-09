import { getApiBase as getApiBaseFromLib } from "@/lib/utils";

export function getApiBase() {
  return getApiBaseFromLib();
}

export type HttpClient = {
  fetch(path: string, options?: RequestInit): Promise<Response>;
};

function forceLogout() {
  try {
    localStorage.removeItem("token");
    localStorage.removeItem("auth_user");
  } catch {}

  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
}

function isAbsoluteUrl(url: string) {
  return /^https?:\/\//i.test(url);
}

function isPublicAuthRoute(path: string) {
  // rotas que podem devolver 401 e o frontend deve tratar (sem auto-logout)
  return (
    path.includes("/auth/login") ||
    path.includes("/auth/register-invite") ||
    path.includes("/auth/validate-invite")
  );
}

export const defaultHttpClient: HttpClient = {
  async fetch(path: string, options: RequestInit = {}) {
    const base = getApiBase();

    const token =
      typeof window !== "undefined" ? localStorage.getItem("token") : null;

    const headers = new Headers(options.headers || {});

    if (token && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    const url = isAbsoluteUrl(path) ? path : `${base}${path}`;

    const res = await fetch(url, {
      ...options,
      headers,
    });

    // 🔐 401 global: derruba sessão para rotas privadas
    if (res.status === 401 && !isPublicAuthRoute(path)) {
      forceLogout();
    }

    // IMPORTANT: retornamos Response (compatível com seu código)
    return res;
  },
};

