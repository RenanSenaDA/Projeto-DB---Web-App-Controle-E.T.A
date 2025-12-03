"use client";

import { useState } from "react";
import { Tabs, TabsContent } from "@/ui/tabs";

import PageHeader from "@/components/header-page";
import TabsListStation from "@/components/tabs-list-station";
import KpiSeriesCard from "@/components/kpi/kpi-series-card";
import KpiSeriesFilter from "@/components/kpi/kpi-serie-filter";

import { MOCK_API_RESPONSE } from "@/lib/mock-data";

// Definição de períodos em minutos
const TIME_RANGES = [
  { label: "Últimos 15 min", value: 15 },
  { label: "Últimas 2h", value: 120 },
  { label: "Últimas 24h", value: 1440 },
  { label: "Últimos 7 dias", value: 10080 },
];

export default function TimeSeriesPage() {
  const etaKpis = MOCK_API_RESPONSE.data.eta.kpis;
  const ultrafiltracaoKpis = MOCK_API_RESPONSE.data.ultrafiltracao.kpis;
  const carvaoKpis = MOCK_API_RESPONSE.data.carvao.kpis;

  const stations = {
    eta: etaKpis,
    ultrafiltracao: ultrafiltracaoKpis,
    carvao: carvaoKpis,
  };

  const [activeStation, setActiveStation] =
    useState<keyof typeof stations>("eta");
  const [selectedFilters, setSelectedFilters] = useState<string[]>([]);
  const [timeRange, setTimeRange] = useState<number>(15); // padrão 15 minutos

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

  // Simula séries temporais filtradas pelo período
  const generateTimeSeries = (kpiId: string, base: number) => {
    const now = Date.now();
    const points = Math.min(Math.ceil(timeRange / 15), 50); // até 50 pontos
    return Array.from({ length: points }).map((_, i) => ({
      timestamp: new Date(now - (points - 1 - i) * 60_000).toLocaleTimeString(
        "pt-BR",
        {
          hour: "2-digit",
          minute: "2-digit",
        }
      ),
      value: base + Math.random() * 10 - 5,
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
        timeSeries={generateTimeSeries(kpi.id, kpi.value ?? 0)} // passa os dados filtrados
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

        {/* Select de período */}
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
          setActiveStation(value as keyof typeof stations)
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
