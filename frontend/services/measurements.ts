import type { HttpClient } from "@/services/http"
import { getApiBase } from "@/lib/utils"

// Tipo: ponto de série temporal retornado pela API
// Campos: ts (ISO timestamp), value (número), unit (opcional)
export type SeriesPoint = { ts: string; value: number; unit?: string | null }
// Mapa de tag para lista de pontos da série
export type SeriesMap = Record<string, SeriesPoint[]>

// Service: opera chamadas de medições
// getSeries(tags, minutes): busca séries para as tags no intervalo em minutos
// Retorna: SeriesMap
// Erros: lança Error em HTTP não-OK
export type MeasurementsService = {
  getSeries: (tags: string[], minutes: number) => Promise<SeriesMap>
}

// Factory: cria service de medições usando HttpClient
export function createMeasurementsService(client: HttpClient): MeasurementsService {
  return {
    async getSeries(tags, minutes) {
      // Justifica cache: no-store para refletir dados em tempo real
      const params = new URLSearchParams({ tags: tags.join(","), minutes: String(minutes) })
      const res = await client.fetch(`${getApiBase()}/measurements/series?${params.toString()}`, { cache: "no-store" })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return (await res.json()) as SeriesMap
    },
  }
}
