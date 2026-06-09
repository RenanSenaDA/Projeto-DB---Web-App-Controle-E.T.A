import { getApiBase as getApiBaseFromLib } from "@/lib/utils";

export function getApiBase() {
  return getApiBaseFromLib();
}

export type HttpClient = {
  fetch(path: string, options?: RequestInit): Promise<Response>;
};

function forceLogout() {
  // Só faz sentido no browser
  if (typeof window === "undefined") return;

  try {
    localStorage.removeItem("token");
    localStorage.removeItem("auth_user");
  } catch {}

  window.location.href = "/login";
}

function isAbsoluteUrl(url: string) {
  return /^https?:\/\//i.test(url);
}

function isPublicAuthRoute(path: string) {
  // Rotas que podem devolver 401 e o frontend deve tratar (sem auto-logout)
  return (
    path.includes("/auth/login") ||
    path.includes("/auth/register-invite") ||
    path.includes("/auth/validate-invite")
  );
}

function getDefaultTimeoutMs() {
  // SSR deve falhar rápido para não travar render
  return typeof window === "undefined" ? 4000 : 8000;
}

function createErrorResponse(message: string, status = 503) {
  return new Response(JSON.stringify({ ok: false, error: message }), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

async function fetchWithTimeout(url: string, options: RequestInit, timeoutMs: number) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  // Se quem chamou já passou signal, respeita (aborta nosso controller junto)
  const externalSignal = options.signal;
  const onAbort = () => controller.abort();

  try {
    if (externalSignal) {
      if (externalSignal.aborted) controller.abort();
      else externalSignal.addEventListener("abort", onAbort, { once: true });
    }

    return await fetch(url, {
      ...options,
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeoutId);
    if (externalSignal) {
      try {
        externalSignal.removeEventListener("abort", onAbort);
      } catch {}
    }
  }
}

function isIdempotentGet(options: RequestInit) {
  const method = (options.method || "GET").toUpperCase();
  return method === "GET";
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

    const timeoutMs = getDefaultTimeoutMs();

    // 1) tentativa normal
    try {
      const res = await fetchWithTimeout(
        url,
        {
          ...options,
          headers,
        },
        timeoutMs
      );

      // 🔐 401 global: derruba sessão para rotas privadas (somente browser)
      if (res.status === 401 && !isPublicAuthRoute(path)) {
        forceLogout();
      }

      return res;
    } catch (err: any) {
      // 2) retry leve somente para GET (erro de rede/timeout)
      if (isIdempotentGet(options)) {
        try {
          const res2 = await fetchWithTimeout(
            url,
            {
              ...options,
              headers,
            },
            timeoutMs
          );

          if (res2.status === 401 && !isPublicAuthRoute(path)) {
            forceLogout();
          }

          return res2;
        } catch {}
      }

      // Mantém contrato retornando Response (evita travas e unhandled)
      const msg =
        err?.name === "AbortError"
          ? `Request timeout (${timeoutMs}ms): ${path}`
          : `Network error: ${path}`;

      return createErrorResponse(msg, 503);
    }
  },
};
