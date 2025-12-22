import type { HttpClient } from "@/services/http";

type LimitsGetResponse = {
  limits: Record<string, number>;
};

type LimitsPutPayload = {
  limits: Record<string, number>;
};

export function createLimitsService(http: HttpClient) {
  return {
    async getAll(): Promise<LimitsGetResponse> {
      const res = await http.fetch("/limits", { method: "GET" });
      if (!res.ok) {
        throw new Error("Falha ao carregar limites");
      }
      return (await res.json()) as LimitsGetResponse;
    },

    /**
     * Atualiza UM limite, reaproveitando o endpoint bulk /limits
     * (envia apenas { limits: { [tag]: valor } } ).
     *
     * IMPORTANTE: aqui o "tag" deve ser o TAG REAL do banco:
     * ex: "bombeamento/vazao", "decantacao/turbidez", etc.
     */
    async updateByTag(tag: string, value: number): Promise<{ ok: boolean }> {
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
