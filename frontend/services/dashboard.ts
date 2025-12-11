import type { HttpClient } from "@/services/http"
import { getApiBase } from "@/lib/utils"
import type { ApiResponse } from "@/types/kpi"

// Service: obtém payload do dashboard
// getDashboard(): retorna estrutura ApiResponse com meta e dados por estação
export type DashboardService = {
  getDashboard: () => Promise<ApiResponse>
}

// Factory: cria service do dashboard usando HttpClient
export function createDashboardService(client: HttpClient): DashboardService {
  return {
    async getDashboard() {
      const res = await client.fetch(`${getApiBase()}/dashboard`, { cache: "no-store" })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return (await res.json()) as ApiResponse
    },
  }
}
