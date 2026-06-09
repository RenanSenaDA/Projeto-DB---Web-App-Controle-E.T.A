import { getApiBase, type HttpClient } from "@/services/http";

/** Saúde de um sensor (espelha GET /sensors/health). */
export type SensorHealth = {
  tag: string;
  unit: string | null;
  last_value: number | null;
  last_ts: string | null;
  age_seconds: number | null;
  status: "online" | "stale";
  suspect: boolean;
  quality: string | null;
  plausible_min: number | null;
  plausible_max: number | null;
};

export function createSensorsService(http: HttpClient) {
  return {
    /** GET /sensors/health — estado de saúde de cada sensor. */
    async getHealth(): Promise<SensorHealth[]> {
      const res = await http.fetch(`${getApiBase()}/sensors/health`, { method: "GET" });
      if (!res.ok) throw new Error("Falha ao carregar saúde dos sensores");
      return (await res.json()) as SensorHealth[];
    },
  };
}
