import type { HttpClient } from "@/services/http";

/**
 * Tipagem da resposta contendo o mapa de limites configurados.
 * A chave (string) é a tag do sensor e o valor (number) é o limite definido.
 */
type LimitsGetResponse = {
  limits: Record<string, number>;
};

/**
 * Estrutura do payload para atualização de limites.
 * Permite enviar um objeto parcial contendo apenas os limites que devem ser alterados.
 */
type LimitsPutPayload = {
  limits: Record<string, number>;
};

/**
 * Serviço responsável pelo gerenciamento de Limites Operacionais (Setpoints/Thresholds).
 * Permite visualizar e alterar os valores máximos/mínimos dos sensores.
 *
 * @param http - Cliente HTTP para realizar as requisições.
 */
export function createLimitsService(http: HttpClient) {
  return {
    /**
     * Busca todos os limites cadastrados no sistema.
     * Endpoint: GET /limits
     *
     * @returns {Promise<LimitsGetResponse>} Objeto contendo o dicionário de limites.
     * @throws {Error} Caso não seja possível carregar os dados.
     */
    async getAll(): Promise<LimitsGetResponse> {
      const res = await http.fetch("/limits", { method: "GET" });
      if (!res.ok) {
        throw new Error("Falha ao carregar limites");
      }
      return (await res.json()) as LimitsGetResponse;
    },

    /**
     * Atualiza o valor de um único limite específico.
     *
     * Estratégia: Utiliza o endpoint de atualização em massa (PUT /limits),
     * mas constrói um payload contendo apenas o item que foi modificado.
     *
     * @param tag - A tag identificadora real do sensor no banco (ex: "bombeamento/vazao").
     * @param value - O novo valor numérico para o limite.
     * @returns {Promise<{ ok: boolean }>} Confirmação da operação.
     */
    async updateByTag(tag: string, value: number): Promise<{ ok: boolean }> {
      // Constrói o objeto parcial: { limits: { "tag_especifica": 123 } }
      const payload: LimitsPutPayload = { limits: { [tag]: value } };

      const res = await http.fetch("/limits", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const txt = await res.text().catch(() => "");
        throw new Error(txt || "Falha ao atualizar limite");
      }
      return (await res.json()) as { ok: boolean };
    },
  };
}