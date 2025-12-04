"use client";
import { Tabs, TabsContent } from "@/ui/tabs";

import KPICard from "@/components/kpi/kpi-card";
import Error from "@/components/feedback/error";
import PageHeader from "@/components/header-page";
import Loading from "@/components/feedback/loading";
import KPISection from "@/components/kpi/kpi-section";
import KPIStatusCard from "@/components/kpi/kpi-status-card";
import TabsListStation from "@/components/tabs-list-station";

import { SECTIONS } from "@/types/kpi";
import type { KPIData, KPICategory } from "@/types/kpi";

import useApi from "@/hooks/use-api";

export default function DashboardPage() {
  const { loading, error, getKPIs, data, fetchData } = useApi();

  if (loading) return <Loading />;
  if (error) return <Error error={error} fetchData={fetchData} />;

  const lastUpdate = data?.meta.timestamp || "--:--:--";

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
    <div className="container mx-auto min-h-screen p-6 font-sans">
      <div className="flex justify-between items-center">
        <PageHeader
          title="Dashboard de Monitoramento"
          subtitle="Visão geral das estações em tempo real"
        />
      </div>

      <Tabs defaultValue="eta" className="w-full">
        <TabsListStation />

        {Object.keys(stations).map((stationKey) => (
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
              const sectionKPIs = getKPIs(
                stationKey as keyof typeof stations,
                category
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
