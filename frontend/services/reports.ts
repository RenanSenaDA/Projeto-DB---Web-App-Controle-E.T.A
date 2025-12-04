import type { HttpClient } from "@/services/http"
import { getApiBase, idToTag } from "@/lib/utils"

export type ReportsService = {
  getExcelRange: (ids: string[], range: { start: string; end: string }) => Promise<Blob>
}

export function createReportsService(client: HttpClient): ReportsService {
  return {
    async getExcelRange(ids, range) {
      const tags = ids.map((id) => idToTag(id)).join(",")
      const params = new URLSearchParams({ start: range.start, end: range.end })
      if (ids.length > 0) params.set("tags", tags)
      const res = await client.fetch(`${getApiBase()}/reports/excel-range?${params.toString()}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return await res.blob()
    },
  }
}
