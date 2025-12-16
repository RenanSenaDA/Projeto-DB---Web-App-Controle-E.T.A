import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import type { ApiResponse } from "@/types/kpi";
import { createDashboardService } from "@/services/dashboard";
import { defaultHttpClient } from "@/services/http";

// Hook: carrega payload do dashboard e expõe utilitários
// Retorno: { data, loading, error, fetchData, getKPIs }
// Erros: seta 'error' e exibe toast quando falha conexão
export default function useApi(initialData?: ApiResponse | null) {
  const [data, setData] = useState<ApiResponse | null>(initialData || null);
  const [loading, setLoading] = useState<boolean>(!initialData);
  const [error, setError] = useState<string | null>(null);

  // Busca dados do dashboard; silent evita estado de loading na UI
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

  useEffect(() => {
    fetchData();
    const interval = setInterval(() => fetchData({ silent: true }), 60000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // Retorna KPIs de uma estação; opcionalmente filtra pela categoria
  const getKPIs = useCallback(
    (stations: string, category?: string) => {
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
