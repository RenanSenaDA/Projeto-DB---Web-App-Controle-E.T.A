import { useCallback, useState } from "react";
import type { KPIData } from "@/types/kpi";

interface DateRange {
  start: string;
  end: string;
}

/**
 * Retorna a data de hoje em formato YYYY-MM-DD usando horário LOCAL (sem UTC),
 * evitando o bug de "voltar 1 dia" por timezone.
 */
function getTodayDateOnly(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

/**
 * ViewModel para a geração de Relatórios.
 * Gerencia o estado do formulário de seleção (KPIs, datas, expansão de acordeão).
 * Puramente gerenciamento de estado local (UI), sem chamadas de API diretas.
 */
export default function useReportViewModel() {
  const [selectedKpis, setSelectedKpis] = useState<string[]>([]);

  const [dateRange, setDateRange] = useState<DateRange>(() => {
    const today = getTodayDateOnly();
    return { start: today, end: today };
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

  const setStartDate = useCallback((date: string) => {
    setDateRange((prev) => ({ ...prev, start: date }));
  }, []);

  const setEndDate = useCallback((date: string) => {
    setDateRange((prev) => ({ ...prev, end: date }));
  }, []);

  const clearAll = useCallback(() => {
    setSelectedKpis([]);
    setExpandedSystems([]);
    const today = getTodayDateOnly();
    setDateRange({ start: today, end: today });
  }, []);

  return {
    selectedKpis,
    dateRange,
    expandedSystems,
    setExpandedSystems,
    toggleKpi,
    toggleSystemAll,
    setStartDate,
    setEndDate,
    clearAll,
  };
}
