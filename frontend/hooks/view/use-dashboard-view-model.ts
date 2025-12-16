import { useMemo } from "react";
import useApi from "@/hooks/api/use-api";
import { buildCategoryMap } from "@/lib/utils";
import type { ApiResponse } from "@/types/kpi";

/**
 * ViewModel para o Dashboard.
 * Responsável por processar os dados brutos da API e preparar as estruturas
 * necessárias para renderização das abas (estações) e seções (categorias).
 *
 * @param initialData - Dados iniciais (SSR) para hidratação
 */
export function useDashboardViewModel(initialData?: ApiResponse | null) {
  // Hook de API base para buscar o payload principal
  const { loading, error, getKPIs, data, fetchData } = useApi(initialData);

  /**
   * Filtra chaves de estações que possuem KPIs.
   * Evita mostrar abas vazias.
   */
  const stationKeys = useMemo(() => {
    return Object.keys(data?.data ?? {}).filter(
      (key) => (data?.data?.[key]?.kpis?.length ?? 0) > 0
    );
  }, [data]);

  /**
   * Lista formatada para o componente de Tabs.
   */
  const stationsList = useMemo(() => {
    return stationKeys.map((key) => ({
      key,
      label: key.toUpperCase(),
    }));
  }, [stationKeys]);

  /**
   * Mapa de categorias (ex: "quimico" -> { label: "Químico", color: "blue" })
   * Construído dinamicamente a partir dos dados.
   */
  const categoryMap = useMemo(() => buildCategoryMap(data), [data]);
  
  const lastUpdate = data?.meta.timestamp || "--:--:--";
  const hasData = stationKeys.length > 0;

  return {
    loading,
    error,
    data,
    fetchData,
    stationKeys,
    stationsList,
    categoryMap,
    lastUpdate,
    getKPIs,
    hasData,
  };
}
