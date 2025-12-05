import type { HttpClient } from "@/services/http"
import { getApiBase } from "@/lib/utils"

export type AlarmsService = {
  getStatus: () => Promise<{ alarms_enabled: boolean }>
  setStatus: (enabled: boolean) => Promise<void>
}

export function createAlarmsService(client: HttpClient): AlarmsService {
  return {
    async getStatus() {
      const res = await client.fetch(`${getApiBase()}/alarms/status`, { cache: "no-store" })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return (await res.json()) as { alarms_enabled: boolean }
    },
    async setStatus(enabled) {
      const res = await client.fetch(`${getApiBase()}/alarms/status`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ alarms_enabled: !!enabled }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
    },
  }
}

