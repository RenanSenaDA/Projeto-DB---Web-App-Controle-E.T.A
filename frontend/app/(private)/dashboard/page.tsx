"use client";

import { useState } from "react";
import { Tabs, TabsContent } from "@/ui/tabs";

import Error from "@/components/feedback/error";
import Loading from "@/components/feedback/loading";
import KPICard from "@/components/kpi/kpi-card";
import PageHeader from "@/components/header-page";
import KPISection from "@/components/kpi/kpi-section";
import KPIStatusCard from "@/components/kpi/kpi-status-card";
import TabsListStation from "@/components/tabs-list-station";

import { SECTIONS } from "@/types/kpi";
import type { KPIData, KPICategory } from "@/types/kpi";

import useApi from "@/hooks/use-api";

// Define períodos em minutos
const TIME_RANGES = [
  { label: "Últimos 15 min", value: 15 },
  { label: "Últimas 2h", value: 120 },
  { label: "Últimas 24h", value: 1440 },
  { label: "Últimos 7 dias", value: 10080 },
];

export default function DashboardPage() {
  const { loading, error, getKPIs, data, fetchData } = useApi();
  const [timeRange, setTimeRange] = useState<number>(15); // padrão 15 minutos

  if (loading) return <Loading />;
  if (error) return <Error error={error} fetchData={fetchData} />;

  const lastUpdate = data?.meta.timestamp || "--:--:--";

  // Aqui você pode filtrar os KPIs que possuem histórico
  // e limitar os dados ao período selecionado
  const filterByTimeRange = (kpis: KPIData[]) => {
    if (!kpis.length) return kpis;

    const now = Date.now();
    const rangeStart = now - timeRange * 60_000;

    return kpis.map((kpi) => {
      if (!kpi.history) return kpi;

      const filteredHistory = kpi.history.filter(
        (point) => new Date(point.timestamp).getTime() >= rangeStart
      );

      return { ...kpi, history: filteredHistory };
    });
  };

  const renderCardList = (kpis: KPIData[]) => {
    if (!kpis.length)
      return (
        <p className="text-sm text-slate-400 italic">Nenhum dado disponível.</p>
      );

    return (
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
        {kpis.map((kpi) => (
          <KPICard
            key={kpi.id}
            {...kpi}
            updated_at={kpi.updated_at ?? lastUpdate}
          />
        ))}
      </div>
    );
  };

  const renderStatusCard = (kpis: KPIData[]) => {
    const item = kpis.find((k) => k.id === "fca_status_filtro");
    if (!item) return null;
    return (
      <div className="mb-4">
        <KPIStatusCard value={item.status_operation ?? null} />
      </div>
    );
  };

  const stations = {
    eta: data?.data.eta.kpis ?? [],
    ultrafiltracao: data?.data.ultrafiltracao.kpis ?? [],
    carvao: data?.data.carvao.kpis ?? [],
  };

  return (
    <div className="container mx-auto min-h-screen p-6 font-sans space-y-6">
      <div className="flex justify-between items-center">
        <PageHeader
          title="Dashboard de Monitoramento"
          subtitle="Visão geral das estações em tempo real"
        />

        {/* Select de período */}
        <div className="flex justify-end mb-4">
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
      </div>

      <Tabs defaultValue="eta" className="w-full">
        <TabsListStation />

        {Object.entries(stations).map(([stationKey, kpis]) => (
          <TabsContent
            key={stationKey}
            value={stationKey}
            className="space-y-8 animate-in fade-in-50 duration-300"
          >
            {(
              Object.entries(SECTIONS) as [
                KPICategory,
                (typeof SECTIONS)[keyof typeof SECTIONS]
              ][]
            ).map(([category, config]) => {
              const sectionKPIs = filterByTimeRange(
                getKPIs(stationKey as keyof typeof stations, category)
              );

              if (!sectionKPIs.length) return null;

              return (
                <KPISection
                  key={category}
                  color={config.color}
                  title_section={config.title}
                >
                  {category === "operacional" && stationKey === "carvao" && (
                    <>
                      {renderStatusCard(sectionKPIs)}
                      {renderCardList(
                        sectionKPIs.filter((k) => k.id !== "fca_status_filtro")
                      )}
                    </>
                  )}

                  {!(category === "operacional" && stationKey === "carvao") &&
                    renderCardList(sectionKPIs)}
                </KPISection>
              );
            })}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
