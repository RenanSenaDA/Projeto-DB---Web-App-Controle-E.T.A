"use client";

import { useMemo, useState } from "react";
import { Tabs, TabsContent } from "@/ui/tabs";
import { Button } from "@/ui/button";
import { SearchX } from "lucide-react";

import Error from "@/components/feedback/error";
import PageHeader from "@/components/header-page";
import Loading from "@/components/feedback/loading";
import TabsListStation from "@/components/tabs-list-station";
import KPISection from "@/components/kpi/kpi-section";
import KpiSeriesCard from "@/components/kpi/kpi-series-card";
import KpiSeriesFilter from "@/components/kpi/kpi-serie-filter";

import useApi from "@/hooks/use-api";
import useSeries from "@/hooks/use-series";
import { buildCategoryMap, idToTag } from "@/lib/utils";
import type { KPIData, ApiResponse } from "@/types/kpi";

const TIME_RANGES = [
  { label: "Últimos 15 min", value: 15 },
  { label: "Últimas 1 h", value: 60 },
  { label: "Últimas 6 h", value: 360 },
  { label: "Últimas 12 h", value: 720 },
  { label: "Últimas 24 h", value: 1440 },
  { label: "Últimos 7 dias", value: 10080 },
  { label: "Últimos 30 dias", value: 43200 },
];

interface TimeSeriesClientProps {
  initialData?: ApiResponse | null;
}

export default function TimeSeriesClient({
  initialData,
}: TimeSeriesClientProps) {
  // Página: séries temporais por estação e categoria
  // Objetivo: construir tags dinâmicas por estação e filtros para chamar a API
  const { data, loading, error, fetchData } = useApi(initialData);

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

  const [activeStation, setActiveStation] = useState<string>("");
  const [selectedFilters, setSelectedFilters] = useState<string[]>([]);
  const [timeRange, setTimeRange] = useState<number>(10080);
  const selectedStation = useMemo(
    () => activeStation || stationKeys[0] || "",
    [activeStation, stationKeys]
  );
  // Define tags ativas: se houver filtros, usa apenas IDs filtrados desta estação
  const activeTags = useMemo(() => {
    const stationKpis = data?.data?.[selectedStation]?.kpis ?? [];
    const stationIds = new Set(stationKpis.map((k) => k.id));
    const ids =
      selectedFilters.length > 0
        ? selectedFilters.filter((id) => stationIds.has(id))
        : stationKpis.map((k) => k.id);
    return ids.map((id) => idToTag(id)).sort();
  }, [selectedStation, data, selectedFilters]);
  const {
    data: seriesMap,
    loading: seriesLoading,
    error: seriesError,
    refresh,
  } = useSeries(activeTags, timeRange);

  const categoryMap = buildCategoryMap(data);

  const noSeries = Object.keys(seriesMap || {}).length === 0;

  const allKpis = useMemo(() => {
    const stations = Object.values(data?.data ?? {});
    const merged = stations.flatMap((s) => s.kpis || []);
    const uniq = new Map<string, (typeof merged)[number]>();
    merged.forEach((k) => uniq.set(k.id, k));
    return Array.from(uniq.values());
  }, [data]);

  if (loading || seriesLoading) return <Loading />;
  if (error) return <Error error={error} fetchData={fetchData} />;
  if (seriesError) return <Error error={seriesError} fetchData={refresh} />;

  // Alterna seleção de um KPI no filtro; reduz chamadas quando filtrado
  const toggleFilter = (kpiId: string) => {
    setSelectedFilters((prev) =>
      prev.includes(kpiId)
        ? prev.filter((id) => id !== kpiId)
        : [...prev, kpiId]
    );
  };

  // Transforma pontos brutos em estrutura para o gráfico (rótulo HH:MM)
  const buildSeries = (tag: string) => {
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

  // Renderiza cartões de série para a lista de KPIs da categoria
  const renderSeries = (kpis: KPIData[]) => {
    const filtered = selectedFilters.length
      ? kpis.filter((k) => selectedFilters.includes(k.id))
      : kpis;

    return filtered.map((kpi) => (
      <KpiSeriesCard
        key={kpi.id}
        kpi={{ ...kpi, value: kpi.value ?? undefined, unit: kpi.unit ?? "" }}
        timeSeries={buildSeries(idToTag(kpi.id))}
      />
    ));
  };

  return (
    <div className="container mx-auto min-h-screen p-6 space-y-6">
      <PageHeader
        title="Séries Temporais de KPIs"
        subtitle="Visualize a evolução dos indicadores por estação"
      >
        <div className="flex items-center gap-2 bg-white p-2 rounded-lg border shadow-sm">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider pl-2">
            Período:
          </span>
          <select
            className="border-none bg-transparent text-sm font-medium focus:ring-0 cursor-pointer outline-none text-slate-700"
            value={timeRange}
            onChange={(e) => setTimeRange(Number(e.target.value))}
          >
            {TIME_RANGES.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </select>
        </div>
      </PageHeader>

      {noSeries && (
        <div className="flex flex-col items-center justify-center py-12 text-center rounded-lg border border-dashed border-slate-300 bg-slate-50/50">
          <div className="bg-slate-100 p-3 rounded-full mb-4">
            <SearchX className="h-8 w-8 text-slate-400" />
          </div>
          <h3 className="text-lg font-medium text-slate-900 mb-1">
            Nenhum dado encontrado
          </h3>
          <p className="text-sm text-slate-500 max-w-sm mx-auto mb-4">
            Não encontramos leituras para o período selecionado. Tente aumentar
            o intervalo de tempo.
          </p>
          {selectedFilters.length > 0 && (
            <Button
              variant="outline"
              onClick={() => setSelectedFilters([])}
              className="text-slate-600 border-slate-300 hover:bg-white"
            >
              Limpar Filtros
            </Button>
          )}
        </div>
      )}

      <KpiSeriesFilter
        allKpis={allKpis}
        selectedFilters={selectedFilters}
        toggleFilter={toggleFilter}
        clearFilters={() => setSelectedFilters([])}
      />

      <Tabs
        value={selectedStation}
        className="w-full mb-4"
        onValueChange={(value) => setActiveStation(value as string)}
      >
        <TabsListStation stations={stationsList} />

        {stationKeys.map((key) => (
          <TabsContent key={key} value={key}>
            {Object.entries(categoryMap).map(([category, config]) => {
              const stationKpis = data?.data?.[key]?.kpis ?? [];
              const sectionItems = stationKpis.filter(
                (k) => k.category === category
              );
              if (!sectionItems.length) return null;

              return (
                <KPISection
                  key={category}
                  color={config.color}
                  title_section={config.title}
                >
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                    {renderSeries(sectionItems)}
                  </div>
                </KPISection>
              );
            })}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
