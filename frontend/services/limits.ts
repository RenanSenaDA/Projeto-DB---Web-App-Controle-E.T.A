import type { HttpClient } from "@/services/http"
import { getApiBase, idToTag } from "@/lib/utils"

/**
 * Serviço de Limites.
 * Gerencia a atualização dos limites operacionais (setpoints) das KPIs.
 */
export type LimitsService = {
  updateById: (id: string, value: number) => Promise<void>
  updateManyByTag: (limits: Record<string, number>) => Promise<void>
}

/**
 * Factory para criar o serviço de Limites.
 * @param client Cliente HTTP injetado
 */
export function createLimitsService(client: HttpClient): LimitsService {
  return {
    /**
     * Atualiza o limite de uma única KPI pelo seu ID.
     * Converte o ID interno para a Tag da API antes de enviar.
     */
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

    /**
     * Atualiza múltiplos limites de uma vez usando um mapa de Tag -> Valor.
     */
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
