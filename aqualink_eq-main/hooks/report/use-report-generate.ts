import type { DashboardResponse } from "@/types/kpi";
import { Factory, Filter, Waves, type LucideIcon } from "lucide-react";
import { useState } from "react";

const SYSTEM_CONFIG: Record<
  string,
  { label: string; icon: LucideIcon; color: string }
> = {
  eta: {
    label: "ETA",
    icon: Factory,
    color: "text-blue-600",
  },
  ultrafiltracao: {
    label: "Ultrafiltração",
    icon: Waves,
    color: "text-blue-600",
  },
  carvao: {
    label: "Filtro de Carvão",
    icon: Filter,
    color: "text-blue-600",
  },
};

export default function useReportGenerator(apiData: DashboardResponse | null) {
  const [isGenerating, setIsGenerating] = useState(false);

  const generateCsv = async (selectedKpis: string[]) => {
    if (selectedKpis.length === 0 || !apiData) return;
    setIsGenerating(true);

    try {
      // Simula processamento
      await new Promise((resolve) => setTimeout(resolve, 2000));

      const headers = "Data,Sistema,KPI,Valor,Unidade,Status\n";

      // Reconstrói os dados para o CSV baseando-se nos IDs selecionados
      const rows = selectedKpis
        .map((kpiId) => {
          let label = kpiId;
          let systemLabel = "-";
          let unit = "-";

          // Busca ineficiente proposital para brevidade (em produção usaríamos um Map)
          Object.entries(apiData.data).forEach(([sysKey, sysData]) => {
            const found = sysData.kpis.find((k) => k.id === kpiId);
            if (found) {
              label = found.label;
              unit = found.unit;
              systemLabel = SYSTEM_CONFIG[sysKey]?.label || sysKey;
            }
          });

          return `${new Date().toLocaleDateString()},${systemLabel},${label},0.00,${unit},Simulado`;
        })
        .join("\n");

      const csvContent = headers + rows;
      const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.setAttribute("href", url);
      link.setAttribute(
        "download",
        `relatorio_monitoramento_${new Date().getTime()}.csv`
      );
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } finally {
      setIsGenerating(false);
    }
  };

  return { isGenerating, generateCsv };
}