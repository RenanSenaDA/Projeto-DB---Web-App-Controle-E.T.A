import type { HttpClient } from "@/services/http"
import { getApiBase } from "@/lib/utils"
import type { ApiResponse } from "@/types/kpi"

/**
 * Serviço de Dashboard.
 * Responsável por obter o payload principal contendo todas as estações e KPIs.
 */
export type DashboardService = {
  getDashboard: () => Promise<ApiResponse>
}

/**
 * Factory para criar o serviço de Dashboard.
 * @param client Cliente HTTP injetado
 */
export function createDashboardService(client: HttpClient): DashboardService {
  return {
    /**
     * Busca os dados completos do dashboard.
     * Retorna a estrutura hierárquica de Estações -> KPIs com valores atuais.
     * Cache configurado como 'no-store' para garantir dados em tempo real.
     */
    async getDashboard() {
      const res = await client.fetch(`${getApiBase()}/dashboard`, { cache: "no-store" })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return (await res.json()) as ApiResponse
    },
  }
}
