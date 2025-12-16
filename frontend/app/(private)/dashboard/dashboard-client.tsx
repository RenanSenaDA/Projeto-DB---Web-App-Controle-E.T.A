"use client";

import { useMemo } from "react";
import { Tabs, TabsContent } from "@/ui/tabs";

import KPICard from "@/components/kpi/kpi-card";
import Error from "@/components/feedback/error";
import PageHeader from "@/components/header-page";
import Loading from "@/components/feedback/loading";
import KPISection from "@/components/kpi/kpi-section";
import TabsListStation from "@/components/tabs-list-station"; 

import type { KPIData, ApiResponse } from "@/types/kpi";
import { buildCategoryMap } from "@/lib/utils";

import useApi from "@/hooks/use-api";

interface DashboardClientProps {
  initialData?: ApiResponse | null;
}

export default function DashboardClient({ initialData }: DashboardClientProps) {
  // Página: visão geral de KPIs por estação/categoria com últimas leituras
  // Recebe initialData do Server Component para hidratação imediata
  const { loading, error, getKPIs, data, fetchData } = useApi(initialData);

  // Deriva lista de estações com KPIs disponíveis do payload
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
  const categoryMap = buildCategoryMap(data);

  if (loading) return <Loading />;
  if (error) return <Error error={error} fetchData={fetchData} />;

  const renderCardList = (kpis: KPIData[]) => {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
        {kpis.map((kpi) => (
          <KPICard
            key={kpi.id}
            {...kpi}
            colorClass={categoryMap[kpi.category]?.color}
            className="h-full"
          />
        ))}
      </div>
    );
  };

  // Status operacional removido; placeholder futuro
  const renderStatusCard = () => null;

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
              {Object.entries(categoryMap).map(([category, config]) => {
                const sectionKPIs = getKPIs(stationKey, category);
                if (!sectionKPIs.length) return null;
                return (
                  <KPISection
                    key={category}
                    color={config.color}
                    title_section={config.title}
                  >
                    {renderStatusCard()}

                    {renderCardList(sectionKPIs)}
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
