"use client";

import { Tabs, TabsContent } from "@/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/ui/select"; // Verifique se o caminho está correto para seu projeto (ex: @/components/ui/select)
import Error from "@/components/feedback/error";
import PageHeader from "@/components/header-page";
import Loading from "@/components/feedback/loading";
import TabsListStation from "@/components/tabs-list-station";
import KPISection from "@/components/kpi/kpi-section";
import KpiSeriesCard from "@/components/kpi/kpi-series-card";
import KpiSeriesFilter from "@/components/kpi/kpi-serie-filter";
import EmptyState from "@/components/feedback/empty-state";

import type { KPIData, ApiResponse } from "@/types/kpi";
import {
  useTimeSeriesViewModel,
  TIME_RANGES,
} from "@/hooks/view/use-time-series-view-model";

interface TimeSeriesClientProps {
  initialData?: ApiResponse | null;
}

/**
 * Componente Cliente de Séries Temporais.
 * Permite visualizar gráficos históricos de KPIs, filtrar por métrica e intervalo de tempo.
 * Gerencia a complexidade de UI através do useTimeSeriesViewModel.
 */
export default function TimeSeriesClient({
  initialData,
}: TimeSeriesClientProps) {
  const {
    loading,
    error,
    fetchData,
    refreshSeries,
    stationKeys,
    stationsList,
    selectedStation,
    setActiveStation,
    timeRange,
    setTimeRange,
    selectedFilters,
    toggleFilter,
    clearFilters,
    noSeries,
    allKpis,
    categoryMap,
    data,
    getSeriesForKpi,
  } = useTimeSeriesViewModel(initialData);

  if (loading) return <Loading />;
  if (error)
    return <Error error={error} fetchData={fetchData || refreshSeries} />;

  const renderSeries = (kpis: KPIData[]) => {
    const filtered = selectedFilters.length
      ? kpis.filter((k) => selectedFilters.includes(k.id))
      : kpis;

    return filtered.map((kpi) => (
      <KpiSeriesCard
        key={kpi.id}
        kpi={{ ...kpi, value: kpi.value ?? null, unit: kpi.unit ?? "" }}
        timeSeries={getSeriesForKpi(kpi.id)}
      />
    ));
  };

  return (
    <div className="container mx-auto min-h-screen p-6 space-y-6">
      <PageHeader
        title="Séries Temporais de KPIs"
        subtitle="Visualize a evolução dos indicadores por estação"
      >
        {/* Container do Select com estilo de "Input Group" */}
        <div className="flex items-center gap-2 bg-card p-1 pr-3 rounded-lg border shadow-sm transition-colors">
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider pl-3">
            Período:
          </span>

          <Select
            value={String(timeRange)}
            onValueChange={(value) => setTimeRange(Number(value))}
          >
            <SelectTrigger className="h-8 border-none bg-transparent shadow-none focus:ring-0 gap-2 w-auto min-w-[140px] text-sm font-medium text-foreground">
              <SelectValue placeholder="Selecione o período" />
            </SelectTrigger>
            <SelectContent>
              {TIME_RANGES.map((r) => (
                <SelectItem key={r.value} value={String(r.value)}>
                  {r.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </PageHeader>

      {noSeries ? (
        <EmptyState
          title="Nenhum dado encontrado"
          description="Não encontramos leituras para o período selecionado. Tente aumentar o intervalo de tempo ou limpar os filtros."
          actionLabel={
            selectedFilters.length > 0 ? "Limpar Filtros" : undefined
          }
          onAction={selectedFilters.length > 0 ? clearFilters : undefined}
        />
      ) : (
        <>
          <KpiSeriesFilter
            allKpis={allKpis}
            selectedFilters={selectedFilters}
            toggleFilter={toggleFilter}
            clearFilters={clearFilters}
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
        </>
      )}
    </div>
  );
}
