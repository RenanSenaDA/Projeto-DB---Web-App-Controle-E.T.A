import { useCallback, useState } from "react";
import type { KPIData } from "@/types/kpi";

interface DateRange {
  start: string;
  end: string;
}

export default function useReportState() {
  const [selectedKpis, setSelectedKpis] = useState<string[]>([]);
  const [dateRange, setDateRange] = useState<DateRange>({
    start: new Date().toISOString().split("T")[0],
    end: new Date().toISOString().split("T")[0],
  });
  const [expandedSystems, setExpandedSystems] = useState<string[]>([]);

  const toggleKpi = useCallback((kpiId: string) => {
    setSelectedKpis((prev) =>
      prev.includes(kpiId)
        ? prev.filter((id) => id !== kpiId)
        : [...prev, kpiId]
    );
  }, []);

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
