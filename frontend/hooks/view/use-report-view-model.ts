import { useCallback, useState } from "react";
import type { KPIData } from "@/types/kpi";

interface DateRange {
  start: string;
  end: string;
}

/**
 * ViewModel para a geração de Relatórios.
 * Gerencia o estado do formulário de seleção (KPIs, datas, expansão de acordeão).
 * Puramente gerenciamento de estado local (UI), sem chamadas de API diretas.
 */
export default function useReportViewModel() {
  const [selectedKpis, setSelectedKpis] = useState<string[]>([]);
  const [dateRange, setDateRange] = useState<DateRange>({
    start: new Date().toISOString().split("T")[0],
    end: new Date().toISOString().split("T")[0],
  });
  const [expandedSystems, setExpandedSystems] = useState<string[]>([]);

  // Alterna seleção de uma única KPI
  const toggleKpi = useCallback((kpiId: string) => {
    setSelectedKpis((prev) =>
      prev.includes(kpiId)
        ? prev.filter((id) => id !== kpiId)
        : [...prev, kpiId]
    );
  }, []);

  /**
   * Alterna seleção de TODAS as KPIs de um sistema/estação.
   * - Se todas já estiverem selecionadas -> Remove todas.
   * - Caso contrário -> Adiciona as que faltam.
   */
  const toggleSystemAll = useCallback((systemKpis: KPIData[]) => {
    const allIds = systemKpis.map((k) => k.id);
    setSelectedKpis((prev) => {
      const allSelected = allIds.every((id) => prev.includes(id));
      return allSelected
        ? prev.filter((id) => !allIds.includes(id))
        : [...new Set([...prev, ...allIds])];
    });
  }, []);

  return {
    selectedKpis,
    dateRange,
    expandedSystems,
    setExpandedSystems,
    toggleKpi,
    toggleSystemAll,
    setStartDate: (date: string) =>
      setDateRange((prev) => ({ ...prev, start: date })),
    setEndDate: (date: string) =>
      setDateRange((prev) => ({ ...prev, end: date })),
    clearAll: () => {
      setSelectedKpis([]);
      setExpandedSystems([]);
      const today = new Date().toISOString().split("T")[0];
      setDateRange({ start: today, end: today });
    },
  };
}
