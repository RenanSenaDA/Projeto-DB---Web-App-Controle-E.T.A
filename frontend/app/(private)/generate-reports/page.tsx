"use client";

import { CheckSquare, Calendar } from "lucide-react";

import { Accordion } from "@/ui/accordion";

import Error from "@/components/feedback/error";
import Loading from "@/components/feedback/loading";

import PageHeader from "@/components/header-page";
import SummaryCard from "@/components/gererate-reposts/summary-card";
import DateRangePicker from "@/components/gererate-reposts/date-range-picker";
import StepAccordionItem from "@/components/gererate-reposts/step-accordion-item";

import useApi from "@/hooks/use-api";
import useReportState from "@/hooks/report/use-report-state";
import useReportGenerator from "@/hooks/report/use-report-generate";

export default function ReportsPage() {
  const { data, loading, error, fetchData } = useApi();

  const {
    selectedKpis,
    dateRange,
    expandedSystems,
    setExpandedSystems,
    toggleKpi,
    toggleSystemAll,
    setStartDate,
    setEndDate,
    clearAll,
  } = useReportState();
  const { isGenerating, generateExcel } = useReportGenerator(data);

  if (loading) return <Loading />;

  if (error) return <Error error={error} fetchData={fetchData} />;

  if (!data) return null;

  return (
    <div className="container mx-auto min-h-screen p-6 font-sans">
      <PageHeader
        title="Relatórios Personalizados"
        subtitle="Selecione as métricas e o período desejado para exportar os dados"
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2 px-1">
            <Calendar className="h-5 w-5 text-slate-400" />
            Período Do Relatório
          </h2>

          <DateRangePicker
            start={dateRange.start}
            end={dateRange.end}
            onStartChange={setStartDate}
            onEndChange={setEndDate}
          />

          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2 px-1">
              <CheckSquare className="h-5 w-5 text-slate-400" />
              Seleção de Métricas
            </h2>

            <Accordion
              type="multiple"
              value={expandedSystems}
              onValueChange={setExpandedSystems}
              className="space-y-4"
            >
              {Object.entries(data.data).map(([key, systemData]) => (
                <StepAccordionItem
                  key={key}
                  systemKey={key}
                  kpis={systemData.kpis}
                  selectedKpis={selectedKpis}
                  onToggleSystemAll={toggleSystemAll}
                  onToggleKpi={toggleKpi}
                />
              ))}
            </Accordion>
          </div>
        </div>

        <div className="lg:col-span-1">
          <SummaryCard
            selectedCount={selectedKpis.length}
            dateRange={dateRange}
            onGenerate={() => {
              void generateExcel(selectedKpis, dateRange).then(() => {
                clearAll();
              });
            }}
            isGenerating={isGenerating}
            isDisabled={loading || !!error}
          />
        </div>
      </div>
    </div>
  );
}
