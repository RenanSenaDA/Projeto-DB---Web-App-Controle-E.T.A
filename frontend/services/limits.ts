import type { HttpClient } from "@/services/http"
import { getApiBase, idToTag } from "@/lib/utils"

export type LimitsService = {
  updateById: (id: string, value: number) => Promise<void>
  updateManyByTag: (limits: Record<string, number>) => Promise<void>
}

export function createLimitsService(client: HttpClient): LimitsService {
  return {
    async updateById(id, value) {
      const tag = idToTag(id)
      const body = { limits: { [tag]: Number(value) } }
      const res = await client.fetch(`${getApiBase()}/limits`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
    },
    async updateManyByTag(limits) {
      const res = await client.fetch(`${getApiBase()}/limits`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ limits }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
    },
  }
}
