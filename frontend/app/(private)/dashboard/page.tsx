"use client";

import { useMemo } from "react";
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

  const lastUpdate = data?.meta.timestamp || "--:--:--";

  if (loading) return <Loading />;
  if (error) return <Error error={error} fetchData={fetchData} />;

  const renderCardList = (kpis: KPIData[]) => {
    if (!kpis.length) {
      return (
        <p className="text-sm text-slate-400 italic">Nenhum dado disponível.</p>
      );
    }

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

  return (
    <div className="container mx-auto min-h-screen p-6 font-sans">
      <div className="flex justify-between items-center">
        <PageHeader
          title="Dashboard de Monitoramento"
          subtitle="Visão geral das estações em tempo real"
        />
      </div>

      {stationKeys.length > 0 ? (
        <Tabs defaultValue={stationKeys[0]} className="w-full">
          <TabsListStation stations={stationsList} />

          {stationKeys.map((stationKey) => (
            <TabsContent
              key={stationKey}
              value={stationKey}
              className="space-y-8 animate-in fade-in-50 duration-300"
            >
              {(Object.keys(SECTIONS) as KPICategory[]).map((category) => {
                const config = SECTIONS[category];
                const sectionKPIs = getKPIs(stationKey, category);

                if (!sectionKPIs.length) return null;

                const isCarvaoOperacional =
                  category === "operacional" && stationKey === "carvao";

                return (
                  <KPISection
                    key={category}
                    color={config.color}
                    title_section={config.title}
                  >
                    {isCarvaoOperacional && renderStatusCard(sectionKPIs)}

                    {renderCardList(
                      isCarvaoOperacional
                        ? sectionKPIs.filter(
                            (k) => k.id !== "fca_status_filtro"
                          )
                        : sectionKPIs
                    )}
                  </KPISection>
                );
              })}
            </TabsContent>
          ))}
        </Tabs>
      ) : (
        <div className="mt-10 text-center">
          <p className="text-sm text-slate-400 italic">
            Nenhum dado de estação disponível no momento.
          </p>
        </div>
      )}
    </div>
  );
}
