import { useMemo, useCallback } from "react";
import useApi from "@/hooks/api/use-api";
import type { ApiResponse, KPIData } from "@/types/kpi";
import { buildCategoryMap } from "@/lib/utils";

/**
 * Labels exibidos nas tabs, mantendo as chaves internas (keys) sem acento.
 */
const STATION_LABELS: Record<string, string> = {
  eta: "ETA",
  ultrafiltracao: "ULTRAFILTRAÇÃO",
  carvao: "CARVÃO",
};

function inferCategoryFromLabel(label: any): string | null {
  const raw = String(label ?? "").trim();
  if (!raw.includes("/")) return null;

  const parts = raw.split("/").filter(Boolean);
  // esperado: ["eta", "operacional", "Fluxo ..."]
  if (parts.length >= 2) return parts[1]; // categoria = 2º segmento
  return null;
}

/**
 * ViewModel para o Dashboard.
 * Organiza KPIs por estação (tabs) e por categoria (seções).
 */
export function useDashboardViewModel(initialData?: ApiResponse | null) {
  const { loading, error, data, fetchData } = useApi(initialData);

  const stationKeys = useMemo(() => {
    return Object.keys(data?.data ?? {}).filter(
      (key) => (data?.data?.[key]?.kpis?.length ?? 0) > 0
    );
  }, [data]);

  const stationsList = useMemo(() => {
    return stationKeys.map((key) => ({
      key,
      label: STATION_LABELS[key] ?? key.toUpperCase(),
    }));
  }, [stationKeys]);

  const categoryMap = useMemo(() => {
    return data ? buildCategoryMap(data) : {};
  }, [data]);

  const hasData = useMemo(() => {
    return stationKeys.length > 0;
  }, [stationKeys]);

  const getKPIs = useCallback(
    (stationKey: string, categoryId: string): KPIData[] => {
      const list = data?.data?.[stationKey]?.kpis ?? [];

      return list.filter((k) => {
        // 1) caminho original (categoria já vem do backend)
        if (k.category === categoryId) return true;

        // 2) fallback: deriva categoria pelo label/tag (eta/operacional/...)
        const inferred = inferCategoryFromLabel(k.label);
        return inferred === categoryId;
      });
    },
    [data]
  );

  return {
    loading,
    error,
    data,
    fetchData,
    stationKeys,
    stationsList,
    categoryMap,
    getKPIs,
    hasData,
  };
}
