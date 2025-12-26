export type HttpClient = {
  fetch: (url: string, init?: RequestInit) => Promise<Response>;
};

/**
 * Retorna a base URL da API.
 * Prioridade:
 * 1. Variável de ambiente (NEXT_PUBLIC_API_BASE_URL)
 * 2. Browser (mesma origem + porta 8000)
 * 3. Fallback (Docker/SSR - http://api:8000)
 */
export function getApiBase(): string {
  const override = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (override) return override;

  if (typeof window !== "undefined") {
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:8000`;
  }

  return "http://api:8000";
}

/**
 * Verifica se uma URL é absoluta (começa com http/https).
 * @param url - A URL a ser verificada.
 */
function isAbsoluteUrl(url: string): boolean {
  return url.startsWith("http://") || url.startsWith("https://");
}

/**
 * Lê cookie pelo nome de forma segura no browser.
 * @param name - Nome do cookie a ser lido.
 * @returns Valor do cookie ou null se não encontrado.
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
 * Recupera o token de autenticação.
 * Prioriza o Cookie (seguro/httpOnly), mas mantém fallback para localStorage
 * para compatibilidade com versões anteriores ou sessões antigas.
 */
function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;

  // 1. Tenta ler do Cookie (Padrão atual)
  const fromCookie = getCookie("auth_token");
  if (fromCookie && fromCookie.trim()) return fromCookie.trim();

  // 2. Fallback para LocalStorage (Legado)
  const fromLs =
    localStorage.getItem("auth_token") ||
    localStorage.getItem("token") 
    
  return fromLs?.trim() || null;
}

/**
 * HttpClient padrão para uso no Client-Side.
 * Injeta automaticamente o token de autorização via Header.
 */
export const defaultHttpClient = {
  fetch: async (url: string, init?: RequestInit) => {
    const headers = new Headers(init?.headers || undefined);

    const token = getAuthToken();
    if (token && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    const finalUrl = isAbsoluteUrl(url)
      ? url
      : `${getApiBase()}${url.startsWith("/") ? url : `/${url}`}`;

    return fetch(finalUrl, {
      ...init,
      headers,
    });
  },
};
