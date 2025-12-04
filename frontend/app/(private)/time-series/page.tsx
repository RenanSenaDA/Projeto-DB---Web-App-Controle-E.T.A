"use client";

import { useMemo, useState } from "react";
import { Tabs, TabsContent } from "@/ui/tabs";

import Error from "@/components/feedback/error";
import PageHeader from "@/components/header-page";
import Loading from "@/components/feedback/loading";
import TabsListStation from "@/components/tabs-list-station";
import KpiSeriesCard from "@/components/kpi/kpi-series-card";
import KpiSeriesFilter from "@/components/kpi/kpi-serie-filter";

import useApi from "@/hooks/use-api";
import useSeries from "@/hooks/use-series";

const TIME_RANGES = [
  { label: "Últimos 15 min", value: 15 },
  { label: "Últimas 1 h", value: 60 },
  { label: "Últimas 6 h", value: 360 },
  { label: "Últimas 12 h", value: 720 },
  { label: "Últimas 24 h", value: 1440 },
  { label: "Últimos 7 dias", value: 10080 },
  { label: "Últimos 30 dias", value: 43200 },
];

export default function TimeSeriesPage() {
  const { data, loading, error, fetchData } = useApi();
  const etaKpis = useMemo(() => data?.data.eta.kpis ?? [], [data]);
  const ultrafiltracaoKpis = useMemo(
    () => data?.data.ultrafiltracao.kpis ?? [],
    [data]
  );
  const carvaoKpis = useMemo(() => data?.data.carvao.kpis ?? [], [data]);

  type StationKey = "eta" | "ultrafiltracao" | "carvao";

  const [activeStation, setActiveStation] = useState<StationKey>("eta");
  const [selectedFilters, setSelectedFilters] = useState<string[]>([]);
  const [timeRange, setTimeRange] = useState<number>(1440);
  const activeTags = useMemo(() => {
    const kpis =
      activeStation === "eta"
        ? etaKpis
        : activeStation === "ultrafiltracao"
        ? ultrafiltracaoKpis
        : carvaoKpis;
    return (kpis || [])
      .map((k) => k.id.replace(/_/g, "/"))
      .sort();
  }, [activeStation, etaKpis, ultrafiltracaoKpis, carvaoKpis]);
  const {
    data: seriesMap,
    loading: seriesLoading,
    error: seriesError,
    refresh,
  } = useSeries(activeTags, timeRange);

  if (loading || seriesLoading) return <Loading />;
  if (error) return <Error error={error} fetchData={fetchData} />;
  if (seriesError) return <Error error={seriesError} fetchData={refresh} />;

  const toggleFilter = (kpiId: string) => {
    setSelectedFilters((prev) =>
      prev.includes(kpiId)
        ? prev.filter((id) => id !== kpiId)
        : [...prev, kpiId]
    );
  };

  const allKpis = Array.from(
    new Map<string, (typeof etaKpis)[number]>([
      ...etaKpis.map((k) => [k.id, k] as [string, (typeof etaKpis)[number]]),
      ...ultrafiltracaoKpis.map(
        (k) => [k.id, k] as [string, (typeof etaKpis)[number]]
      ),
      ...carvaoKpis.map((k) => [k.id, k] as [string, (typeof etaKpis)[number]]),
    ]).values()
  );

  const buildSeries = (tag: string) => {
    const points = seriesMap[tag] || [];
    return points.map((p) => ({
      timestamp: new Date(p.ts).toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit",
      }),
      value: p.value,
    }));
  };

  const renderSeries = (kpis: typeof etaKpis) => {
    const filtered = selectedFilters.length
      ? kpis.filter((k) => selectedFilters.includes(k.id))
      : kpis;

    return filtered.map((kpi) => (
      <KpiSeriesCard
        key={kpi.id}
        kpi={{ ...kpi, value: kpi.value ?? undefined, unit: kpi.unit ?? "" }}
        timeSeries={buildSeries(kpi.id.replace(/_/g, "/"))}
      />
    ));
  };

  return (
    <div className="container mx-auto min-h-screen p-6 space-y-6">
      <div className="flex justify-between items-center">
        <PageHeader
          title="Séries Temporais de KPIs"
          subtitle="Visualize a evolução dos indicadores por estação"
        />

        <select
          className="border rounded px-3 py-1"
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

      <KpiSeriesFilter
        allKpis={allKpis}
        selectedFilters={selectedFilters}
        toggleFilter={toggleFilter}
        clearFilters={() => setSelectedFilters([])}
      />

      <Tabs
        defaultValue="eta"
        className="w-full border-b border-gray-300 mb-4"
        onValueChange={(value) =>
          setActiveStation(value as StationKey)
        }
      >
        <TabsListStation />

        <TabsContent
          value="eta"
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {renderSeries(etaKpis)}
        </TabsContent>

        <TabsContent
          value="ultrafiltracao"
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {renderSeries(ultrafiltracaoKpis)}
        </TabsContent>

        <TabsContent
          value="carvao"
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {renderSeries(carvaoKpis)}
        </TabsContent>
      </Tabs>
    </div>
  );
}
