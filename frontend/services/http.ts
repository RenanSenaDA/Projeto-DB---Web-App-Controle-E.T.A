/**
 * Interface para abstração de cliente HTTP.
 * Permite trocar a implementação (fetch, axios, mock) sem afetar os serviços.
 */
export type HttpClient = {
  fetch: (url: string, init?: RequestInit) => Promise<Response>
}

/**
 * Cliente HTTP padrão usando a Fetch API nativa do navegador/Node.js.
 */
export const defaultHttpClient: HttpClient = {
  fetch: (url, init) => fetch(url, init),
}
