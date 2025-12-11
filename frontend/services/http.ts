// Abstração mínima de cliente HTTP para facilitar testes e troca de implementação
// fetch(url, init?): delega para window.fetch
export type HttpClient = {
  fetch: (url: string, init?: RequestInit) => Promise<Response>
}

// Cliente padrão: usa fetch nativo do navegador
export const defaultHttpClient: HttpClient = {
  fetch: (url, init) => fetch(url, init),
}
