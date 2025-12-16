import { useMemo, useState } from "react";
import useApi from "@/hooks/api/use-api";
import useSeries from "@/hooks/api/use-series";
import { buildCategoryMap, idToTag } from "@/lib/utils";
import type { ApiResponse } from "@/types/kpi";

// Opções de intervalo de tempo para o filtro
export const TIME_RANGES = [
  { label: "Últimos 15 min", value: 15 },
  { label: "Últimas 1 h", value: 60 },
  { label: "Últimas 6 h", value: 360 },
  { label: "Últimas 12 h", value: 720 },
  { label: "Últimas 24 h", value: 1440 },
  { label: "Últimos 7 dias", value: 10080 },
  { label: "Últimos 30 dias", value: 43200 },
];

/**
 * ViewModel para a página de Séries Temporais.
 * Gerencia a seleção de estação, filtros de KPI, intervalo de tempo
 * e coordena o carregamento lazy dos dados históricos.
 */
export function useTimeSeriesViewModel(initialData?: ApiResponse | null) {
  // 1. Carrega dados estruturais (quais estações e KPIs existem)
  const { data, loading: apiLoading, error: apiError, fetchData } = useApi(initialData);
  
  // Estado local da View
  const [activeStation, setActiveStation] = useState<string>("");
  const [selectedFilters, setSelectedFilters] = useState<string[]>([]); // IDs das KPIs selecionadas
  const [timeRange, setTimeRange] = useState<number>(10080); // Default: 7 dias

  // --- Computed Data (Derivados) ---

  // Lista de estações disponíveis (com KPIs)
  const stationKeys = useMemo(() => {
    return Object.keys(data?.data ?? {}).filter(
      (key) => (data?.data?.[key]?.kpis?.length ?? 0) > 0
    );
  }, [data]);

  const stationsList = useMemo(() => {
    return stationKeys.map((key) => ({
      key,
      label: key.toUpperCase(),
    }));
  }, [stationKeys]);

  // Estação selecionada (fallback para a primeira se vazia)
  const selectedStation = useMemo(
    () => activeStation || stationKeys[0] || "",
    [activeStation, stationKeys]
  );

  /**
   * Determina quais Tags devem ser buscadas na API de séries.
   * Lógica:
   * 1. Pega todas as KPIs da estação atual.
   * 2. Se houver filtros selecionados, usa a interseção (Filtros ∩ Estação).
   * 3. Se não houver filtros, pega TODAS as KPIs da estação.
   * 4. Converte ID -> Tag (formato da API).
   */
  const activeTags = useMemo(() => {
    const stationKpis = data?.data?.[selectedStation]?.kpis ?? [];
    const stationIds = new Set(stationKpis.map((k) => k.id));
    const ids = selectedFilters.length > 0
      ? selectedFilters.filter((id) => stationIds.has(id))
      : stationKpis.map((k) => k.id);
    return ids.map((id) => idToTag(id)).sort();
  }, [selectedStation, data, selectedFilters]);

  // 2. Carrega as séries temporais baseadas nas tags ativas
  const {
    data: seriesMap,
    loading: seriesLoading,
    error: seriesError,
    refresh: refreshSeries,
  } = useSeries(activeTags, timeRange);

  const categoryMap = useMemo(() => buildCategoryMap(data), [data]);
  const noSeries = Object.keys(seriesMap || {}).length === 0;

  // Lista plana de todas as KPIs para facilitar busca/filtro
  const allKpis = useMemo(() => {
    const stations = Object.values(data?.data ?? {});
    const merged = stations.flatMap((s) => s.kpis || []);
    const uniq = new Map<string, typeof merged[number]>();
    merged.forEach((k) => uniq.set(k.id, k));
    return Array.from(uniq.values());
  }, [data]);

  // --- Actions ---

  const toggleFilter = (kpiId: string) => {
    setSelectedFilters((prev) =>
      prev.includes(kpiId)
        ? prev.filter((id) => id !== kpiId)
        : [...prev, kpiId]
    );
  };

  const clearFilters = () => setSelectedFilters([]);

  /**
   * Transforma os pontos de dados brutos para o formato do gráfico.
   * Converte timestamp para label legível (HH:MM).
   */
  const getSeriesForKpi = (kpiId: string) => {
    const tag = idToTag(kpiId);
    const points = seriesMap[tag] || [];
    return points.map((p) => ({
      ts: p.ts,
      label: new Date(p.ts).toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit",
      }),
      value: p.value,
    }));
  };

  return {
    // State
    loading: apiLoading || seriesLoading,
    error: apiError || seriesError,
    data,
    stationKeys,
    stationsList,
    categoryMap,
    selectedStation,
    setActiveStation,
    selectedFilters,
    timeRange,
    setTimeRange,
    noSeries,
    
    // Actions & Helpers
    fetchData,
    toggleFilter,
    clearFilters,
    getSeriesForKpi,
    refreshSeries,
    allKpis,
    activeTagsCount: activeTags.length,
  };
}
