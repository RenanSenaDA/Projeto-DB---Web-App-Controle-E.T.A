import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import type { ApiResponse } from "@/types/kpi";
import { createDashboardService } from "@/services/dashboard";
import { defaultHttpClient } from "@/services/http";

/**
 * Hook principal de API.
 * Responsável por buscar o payload mestre do dashboard, que contém a estrutura
 * de estações, categorias e KPIs, além dos valores mais recentes.
 *
 * @param initialData - Dados iniciais opcionais (ex: vindos de SSR)
 */
export default function useApi(initialData?: ApiResponse | null) {
  const [data, setData] = useState<ApiResponse | null>(initialData || null);
  const [loading, setLoading] = useState<boolean>(!initialData);
  const [error, setError] = useState<string | null>(null);

  /**
   * Busca dados do dashboard.
   * @param opts.silent - Se true, não aciona o estado de loading global (útil para polling).
   */
  const fetchData = useCallback(async (opts?: { silent?: boolean }) => {
    // Se já temos dados e é a primeira renderização (não silent), não mostramos loading
    // Mas se for refresh manual, mostramos
    setLoading(opts?.silent ? false : true);
    setError(null);
    try {
      const svc = createDashboardService(defaultHttpClient);
      const json = await svc.getDashboard();
      setData(json as ApiResponse);
    } catch (err) {
      console.error("Erro na API:", err);
      const msg = "Não foi possível conectar ao servidor de dados.";
      setError(msg);
      if (!opts?.silent) toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  // Polling automático a cada 60 segundos
  useEffect(() => {
    fetchData();
    const interval = setInterval(() => fetchData({ silent: true }), 60000);
    return () => clearInterval(interval);
  }, [fetchData]);

  /**
   * Helper para filtrar KPIs de uma estação específica.
   * @param stationKey - Chave da estação (ex: "ete_01")
   * @param category - Filtro opcional de categoria (ex: "quimico")
   */
  const getKPIs = useCallback(
    (stationKey: string, category?: string) => {
      if (!data) return [];

      const stationsData = data.data[stationKey];
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
