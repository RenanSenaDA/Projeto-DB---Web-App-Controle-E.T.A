import { getApiBase, type HttpClient } from "@/services/http";

export type AlarmKind = "high" | "low" | "stale";
export type AlarmStatus = "open" | "acked" | "resolved";

/** Um evento do histórico de alarmes (eta.alarm_event). */
export type AlarmEvent = {
  id: number;
  tag: string;
  kind: AlarmKind;
  severity: string;
  status: AlarmStatus;
  value: number | null;
  threshold: number | null;
  message: string | null;
  opened_at: string;
  acked_at: string | null;
  resolved_at: string | null;
};

/** Faixa de alarme de uma tag (eta.config_limites). */
export type AlarmLimit = {
  tag: string;
  limite: number | null;
  limite_min: number | null;
  limite_max: number | null;
  label: string | null;
};

export type LimitRangeInput = {
  limite_min?: number | null;
  limite_max?: number | null;
  label?: string | null;
};

/**
 * Serviço de alarmes (histórico + faixas). Padrão Factory com injeção do HttpClient.
 */
export function createAlarmHistoryService(http: HttpClient) {
  return {
    /** GET /alarms/events — histórico (filtro opcional por status). */
    async getEvents(status?: string, limit = 100): Promise<AlarmEvent[]> {
      const qs = new URLSearchParams();
      if (status) qs.set("status", status);
      qs.set("limit", String(limit));
      const res = await http.fetch(`${getApiBase()}/alarms/events?${qs.toString()}`, {
        method: "GET",
      });
      if (!res.ok) throw new Error("Falha ao carregar histórico de alarmes");
      return (await res.json()) as AlarmEvent[];
    },

    /** POST /alarms/events/{id}/ack — reconhece um alarme. */
    async ackEvent(id: number): Promise<{ ok: boolean }> {
      const res = await http.fetch(`${getApiBase()}/alarms/events/${id}/ack`, {
        method: "POST",
      });
      if (!res.ok) throw new Error("Falha ao reconhecer alarme");
      return (await res.json()) as { ok: boolean };
    },

    /** GET /alarms/limits — faixas por tag. */
    async getLimits(): Promise<AlarmLimit[]> {
      const res = await http.fetch(`${getApiBase()}/alarms/limits`, { method: "GET" });
      if (!res.ok) throw new Error("Falha ao carregar faixas de alarme");
      return (await res.json()) as AlarmLimit[];
    },

    /** PUT /alarms/limits — upsert das faixas (cada tag substituída pelo objeto). */
    async putLimits(
      ranges: Record<string, LimitRangeInput>
    ): Promise<{ ok: boolean; updated_count: number }> {
      const res = await http.fetch(`${getApiBase()}/alarms/limits`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ranges }),
      });
      if (!res.ok) throw new Error("Falha ao salvar faixas de alarme");
      return (await res.json()) as { ok: boolean; updated_count: number };
    },
  };
}
