import type { ApiResponse } from "@/types/kpi";
import { useState } from "react";
import { toast } from "sonner";
import { createReportsService } from "@/services/reports";
import { defaultHttpClient } from "@/services/http";

/**
 * Hook responsável pela geração de relatórios Excel.
 * Interage com o serviço de relatórios para obter o blob do arquivo e disparar o download no navegador.
 * 
 * @param apiData Dados atuais da API para validação prévia (opcional)
 */
export default function useReportGenerator(apiData: ApiResponse | null) {
  const [isGenerating, setIsGenerating] = useState(false);

  /**
   * Gera e inicia o download do relatório Excel.
   * Cria uma URL temporária para o blob recebido e simula um clique em link.
   * 
   * @param selectedKpis Lista de IDs das KPIs a incluir
   * @param dateRange Intervalo de datas (início e fim)
   */
  const generateExcel = async (
    selectedKpis: string[],
    dateRange: { start: string; end: string }
  ) => {
    if (!apiData) return false;
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
      toast.success("Relatório gerado com sucesso");
      return true;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Erro ao gerar relatório";
      if (msg.includes("404")) {
        toast.error("Não há dados para o período selecionado.");
      } else {
        toast.error(msg);
      }
      return false;
    } finally {
      setIsGenerating(false);
    }
  };

  return { isGenerating, generateExcel };
}
