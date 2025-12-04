import type { HttpClient } from "@/services/http"
import { getApiBase } from "@/lib/utils"
import type { DashboardResponse } from "@/types/kpi"

export type DashboardService = {
  getDashboard: () => Promise<DashboardResponse>
}

export function createDashboardService(client: HttpClient): DashboardService {
  return {
    async getDashboard() {
      const res = await client.fetch(`${getApiBase()}/dashboard`, { cache: "no-store" })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return (await res.json()) as DashboardResponse
    },
  }
}
