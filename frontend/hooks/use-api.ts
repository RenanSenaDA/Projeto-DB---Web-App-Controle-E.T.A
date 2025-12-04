import { useState, useEffect, useCallback } from "react";
import type { DashboardResponse, KPICategory } from "@/types/kpi";
import { createDashboardService } from "@/services/dashboard";
import { defaultHttpClient } from "@/services/http";

export default function useApi() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async (opts?: { silent?: boolean }) => {
    setLoading(opts?.silent ? false : true);
    setError(null);
    try {
      const svc = createDashboardService(defaultHttpClient);
      const json = await svc.getDashboard();
      setData(json as DashboardResponse);
    } catch (err) {
      console.error("Erro na API:", err);
      setError("Não foi possível conectar ao servidor de dados.");
    } finally {
      setLoading(false);
    }
  }, []);

  // Efeito de montagem e polling
  useEffect(() => {
    fetchData();
    const interval = setInterval(() => fetchData({ silent: true }), 60000);
    return () => clearInterval(interval);
  }, [fetchData]);

  /**
   * Utilitário para filtrar KPIs na UI de forma limpa
   */
  const getKPIs = useCallback(
    (stations: "eta" | "ultrafiltracao" | "carvao", category?: KPICategory) => {
      if (!data) return [];

      const stationsData = data.data[stations];
      if (!stationsData) return [];

      const kpis = stationsData.kpis;

      if (!category) return kpis;

      return kpis.filter((kpi) => kpi.category === category);
    },
    [data]
  );

  return {
    data,
    loading,
    error,
    fetchData,
    getKPIs,
  };
}
