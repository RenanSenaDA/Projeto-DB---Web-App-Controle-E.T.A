export type HttpClient = {
  fetch: (url: string, init?: RequestInit) => Promise<Response>
}

export const defaultHttpClient: HttpClient = {
  fetch: (url, init) => fetch(url, init),
}
