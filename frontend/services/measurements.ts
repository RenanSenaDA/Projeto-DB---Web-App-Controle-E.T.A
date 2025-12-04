import type { HttpClient } from "@/services/http"
import { getApiBase } from "@/lib/utils"

export type SeriesPoint = { ts: string; value: number; unit?: string | null }
export type SeriesMap = Record<string, SeriesPoint[]>

export type MeasurementsService = {
  getSeries: (tags: string[], minutes: number) => Promise<SeriesMap>
}

export function createMeasurementsService(client: HttpClient): MeasurementsService {
  return {
    async getSeries(tags, minutes) {
      const params = new URLSearchParams({ tags: tags.join(","), minutes: String(minutes) })
      const res = await client.fetch(`${getApiBase()}/measurements/series?${params.toString()}`, { cache: "no-store" })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return (await res.json()) as SeriesMap
    },
  }
}
