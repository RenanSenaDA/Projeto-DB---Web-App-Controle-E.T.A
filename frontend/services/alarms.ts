import { getApiBase, type HttpClient } from "@/services/http";

/**
 * Tipagem da resposta para a consulta de status (GET).
 * Representa o estado atual dos alarmes no servidor.
 */
export type AlarmsStatusResponse = {
  alarms_enabled: boolean;
};

/**
 * Tipagem da resposta após a alteração de status (PUT).
 * Retorna a confirmação da operação e o novo estado.
 */
export type AlarmsSetResponse = {
  ok: boolean;
  alarms_enabled: boolean;
};

/**
 * Serviço responsável pelo gerenciamento de Alarmes.
 * Utiliza o padrão Factory com Injeção de Dependência (http),
 * permitindo que o cliente HTTP seja substituído facilmente em testes unitários.
 *
 * @param http - Cliente HTTP para realizar as requisições (ex: defaultHttpClient)
 */
export function createAlarmsService(http: HttpClient) {
  return {
    /**
     * Busca o estado atual dos alarmes (ativados ou desativados).
     * Endpoint: GET /alarms/status
     * @returns {Promise<AlarmsStatusResponse>} Objeto contendo a flag `alarms_enabled`.
     * @throws {Error} Se a requisição falhar ou não retornar 200 OK.
     */
    async getStatus(): Promise<AlarmsStatusResponse> {
      // getApiBase() é chamado aqui, mas se o HttpClient já tratar base URL, poderia ser apenas "/alarms/status"
      const res = await http.fetch(`${getApiBase()}/alarms/status`, {
        method: "GET",
      });

      if (!res.ok) {
        throw new Error("Falha ao carregar status dos alarmes");
      }

      const json = (await res.json()) as AlarmsStatusResponse;
      return json;
    },

    /**
     * Atualiza o estado dos alarmes (Ativar/Desativar).
     * Endpoint: PUT /alarms/status
     * @param next - O novo estado desejado (true para ativar, false para desativar).
     * @returns {Promise<AlarmsSetResponse>} Objeto de confirmação.
     * @throws {Error} Retorna a mensagem de erro da API (detail) ou uma mensagem genérica.
     */
    async setStatus(next: boolean): Promise<AlarmsSetResponse> {
      const res = await http.fetch(`${getApiBase()}/alarms/status`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ alarms_enabled: next }),
      });

      if (!res.ok) {
        // Tenta extrair a mensagem de erro específica enviada pelo Backend (padrão FastAPI: "detail")
        let detail = "Falha ao atualizar status dos alarmes";
        try {
          const j = await res.json();
          if (typeof j?.detail === "string") detail = j.detail;
        } catch {}

        throw new Error(detail);
      }

      const json = (await res.json()) as AlarmsSetResponse;
      return json;
    },
  };
}
