import type { DashboardResponse } from "@/types/kpi";
import { useState } from "react";
import { createReportsService } from "@/services/reports";
import { defaultHttpClient } from "@/services/http";

export default function useReportGenerator(apiData: DashboardResponse | null) {
  const [isGenerating, setIsGenerating] = useState(false);

  const generateExcel = async (
    selectedKpis: string[],
    dateRange: { start: string; end: string }
  ) => {
    if (!apiData) return;
    setIsGenerating(true);
    try {
      const svc = createReportsService(defaultHttpClient);
      const blob = await svc.getExcelRange(selectedKpis, dateRange);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `relatorio_${dateRange.start}_a_${dateRange.end}.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } finally {
      setIsGenerating(false);
    }
  };

  return { isGenerating, generateExcel };
}
