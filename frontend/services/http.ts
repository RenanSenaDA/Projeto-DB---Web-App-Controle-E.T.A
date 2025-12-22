// frontend/services/http.ts

export type HttpClient = {
  fetch: (url: string, init?: RequestInit) => Promise<Response>;
};

/**
 * Retorna a base URL da API.
 *
 * REGRAS:
 * - Browser: usa SEMPRE o IP/DNS atual + porta 8000
 * - SSR / Docker: usa api:8000
 * - Override explícito via NEXT_PUBLIC_API_URL
 */
export function getApiBase(): string {
  const override = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (override) return override;

  // Browser: mesma origem + porta 8000
  if (typeof window !== "undefined") {
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:8000`;
  }

  // SSR/Docker
  return "http://api:8000";
}

function isAbsoluteUrl(url: string): boolean {
  return url.startsWith("http://") || url.startsWith("https://");
}

/**
 * Lê cookie pelo nome (no browser).
 */
function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;

  const cookies = document.cookie ? document.cookie.split("; ") : [];
  for (const c of cookies) {
    const [k, ...rest] = c.split("=");
    if (k === name) {
      return decodeURIComponent(rest.join("="));
    }
  }
  return null;
}

/**
 * Token do seu sistema:
 * - é salvo no cookie "auth_token" (hooks/auth/use-auth.ts)
 * - pode existir também em localStorage em versões antigas; mantemos fallback.
 */
function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;

  // Fonte principal (SEU CASO)
  const fromCookie = getCookie("auth_token");
  if (fromCookie && fromCookie.trim()) return fromCookie.trim();

  // Fallbacks (se algum dia você mudar)
  const fromLs =
    localStorage.getItem("auth_token") ||
    localStorage.getItem("token") ||
    localStorage.getItem("access_token") ||
    localStorage.getItem("jwt");

  return fromLs?.trim() || null;
}

/**
 * HttpClient padrão.
 * - Injeta Authorization: Bearer <auth_token> automaticamente
 * - Suporta URL absoluta e relativa (evita /http%3A//...)
 */
export const defaultHttpClient: HttpClient = {
  fetch: async (url: string, init?: RequestInit) => {
    const headers = new Headers(init?.headers || undefined);

    // Injeta token
    const token = getAuthToken();
    if (token && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    // Resolve URL final
    const finalUrl = isAbsoluteUrl(url)
      ? url
      : `${getApiBase()}${url.startsWith("/") ? url : `/${url}`}`;

    return fetch(finalUrl, {
      ...init,
      headers,
    });
  },
};
