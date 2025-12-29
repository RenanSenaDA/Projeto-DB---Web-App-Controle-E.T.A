import type { HttpClient } from "@/services/http"
import { getApiBase } from "@/lib/utils"
import type { SeriesMap } from "@/types/time-series"

/**
 * Serviço de Medições.
 * Responsável por buscar dados históricos (séries temporais) para gráficos.
 */
export type MeasurementsService = {
  getSeries: (tags: string[], minutes: number) => Promise<SeriesMap>
}

/**
 * Factory para criar o serviço de Medições.
 * @param client Cliente HTTP injetado
 */
export function createMeasurementsService(client: HttpClient): MeasurementsService {
  return {
    /**
     * Busca séries temporais para uma lista de tags em um intervalo de tempo.
     * @param tags Lista de tags para buscar
     * @param minutes Janela de tempo em minutos (ex: 60 para 1 hora)
     */
    async getSeries(tags, minutes) {
      // Justifica cache: no-store para refletir dados em tempo real
      const params = new URLSearchParams({ tags: tags.join(","), minutes: String(minutes) })
      const res = await client.fetch(`${getApiBase()}/measurements/series?${params.toString()}`, { cache: "no-store" })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return (await res.json()) as SeriesMap
    },
  }
}
