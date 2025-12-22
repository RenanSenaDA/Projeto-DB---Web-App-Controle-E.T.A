import type { HttpClient } from "@/services/http";

export type AlarmsStatusResponse = {
  alarms_enabled: boolean;
};

export type AlarmsSetResponse = {
  ok: boolean;
  alarms_enabled: boolean;
};

export function createAlarmsService(http: HttpClient) {
  return {
    async getStatus(): Promise<AlarmsStatusResponse> {
      const res = await http.fetch("/alarms/status", { method: "GET" });
      if (!res.ok) {
        throw new Error("Falha ao carregar status dos alarmes");
      }
      const json = (await res.json()) as AlarmsStatusResponse;
      return json;
    },

    async setStatus(next: boolean): Promise<AlarmsSetResponse> {
      const res = await http.fetch("/alarms/status", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ alarms_enabled: next }),
      });

      if (!res.ok) {
        // tenta extrair detail do FastAPI
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
