import type { HttpClient } from "@/services/http"
import { getApiBase, idToTag } from "@/lib/utils"

/**
 * Serviço de Relatórios.
 * Gerencia a geração e download de arquivos Excel com dados históricos.
 */
export type ReportsService = {
  getExcelRange: (ids: string[], range: { start: string; end: string }) => Promise<Blob>
}

/**
 * Factory para criar o serviço de Relatórios.
 * @param client Cliente HTTP injetado
 */
export function createReportsService(client: HttpClient): ReportsService {
  return {
    /**
     * Solicita a geração de um relatório Excel para as KPIs selecionadas no período informado.
     * Retorna um Blob contendo o arquivo Excel binário.
     */
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
