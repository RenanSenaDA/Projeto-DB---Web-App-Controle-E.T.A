"use client";

import { Tabs, TabsContent } from "@/ui/tabs";

import KPICard from "@/components/kpi/kpi-card";
import Error from "@/components/feedback/error";
import PageHeader from "@/components/header-page";
import Loading from "@/components/feedback/loading";
import KPISection from "@/components/kpi/kpi-section";
import EmptyState from "@/components/feedback/empty-state";
import TabsListStation from "@/components/tabs-list-station";

import type { KPIData, ApiResponse } from "@/types/kpi";
import { useDashboardViewModel } from "@/hooks/view/use-dashboard-view-model";

interface DashboardClientProps {
  initialData?: ApiResponse | null;
}

/**
 * Componente Cliente do Dashboard.
 * Exibe os cards de KPI organizados por abas de Estação e seções de Categoria.
 * Utiliza o useDashboardViewModel para gerenciar o estado e lógica.
 */
export default function DashboardClient({ initialData }: DashboardClientProps) {
  const {
    loading,
    error,
    fetchData,
    stationKeys,
    stationsList,
    categoryMap,
    getKPIs,
    hasData,
  } = useDashboardViewModel(initialData);

  if (loading) return <Loading />;
  if (error) return <Error error={error} fetchData={fetchData} />;

  // Renderiza a lista de cards de KPI para uma seção específica
  const renderCardList = (kpis: KPIData[]) => (
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

  return (
    <div className="container mx-auto min-h-screen p-6 font-sans">
      <div className="flex justify-between items-center">
        <PageHeader
          title="Dashboard de Monitoramento"
          subtitle="Visão geral das estações em tempo real"
        />
      </div>

      {hasData ? (
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
                    {renderCardList(sectionKPIs)}
                  </KPISection>
                );
              })}
            </TabsContent>
          ))}
        </Tabs>
      ) : (
        <EmptyState
          title="Nenhuma estação disponível"
          description="Não há dados de monitoramento para exibir no momento."
        />
      )}
    </div>
  );
}
