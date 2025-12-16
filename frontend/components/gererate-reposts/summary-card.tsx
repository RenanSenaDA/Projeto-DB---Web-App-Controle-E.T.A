import { cn } from "@/lib/utils";
import { Button } from "@/ui/button";
import { Download, Loader2 } from "lucide-react";

interface DateRange {
  start: string;
  end: string;
}

/**
 * Propriedades do Card de Resumo.
 */
interface SummaryCardProps {
  /** Quantidade de KPIs selecionadas */
  selectedCount: number;
  /** Intervalo de datas selecionado */
  dateRange: DateRange;
  /** Callback para iniciar a geração do relatório */
  onGenerate: () => void;
  /** Indica se o relatório está sendo gerado (loading state) */
  isGenerating: boolean;
  /** Desabilita o botão de geração (ex: erro ou carregando dados) */
  isDisabled: boolean;
}

/**
 * Card fixo (sticky) que exibe o resumo da solicitação de relatório.
 * Mostra contagem de métricas, datas e botão de download.
 * 
 * @component
 */
export default function SummaryCard({
  selectedCount,
  dateRange,
  onGenerate,
  isGenerating,
  isDisabled,
}: SummaryCardProps) {
  return (
    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-lg sticky top-6">
      <h3 className="font-bold text-slate-800 mb-4 pb-4 border-b border-slate-100">
        Resumo da Solicitação
      </h3>

      <div className="space-y-4 text-sm">
        <div className="flex justify-between items-center">
          <span className="text-slate-500">Métricas Selecionadas:</span>
          <span className="font-bold text-secondary-foreground bg-secondary/10 px-2 py-0.5 rounded-full">
            {selectedCount}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-500">Data Início:</span>
          <span className="font-medium text-secondary-foreground">
            {new Date(dateRange.start).toLocaleDateString("pt-BR")}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-500">Data Fim:</span>
          <span className="font-medium text-secondary-foreground">
            {new Date(dateRange.end).toLocaleDateString("pt-BR")}
          </span>
        </div>
      </div>

      <Button
        onClick={onGenerate}
        disabled={isDisabled || selectedCount === 0 || isGenerating}
        className={cn(
          "w-full mt-8 py-3 px-4 rounded-lg flex items-center justify-center gap-2 font-semibold transition-all shadow-md",
          !isDisabled && selectedCount > 0 && !isGenerating
            ? "bg-secondary hover:bg-secondary/90 text-white"
            : "bg-slate-100 text-slate-400 cursor-not-allowed"
        )}
      >
        {isGenerating ? (
          <>
            <Loader2 className="h-5 w-5 animate-spin" />
            Gerando...
          </>
        ) : (
          <>
            <Download className="h-5 w-5" />
            Baixar Relatório
          </>
        )}
      </Button>
    </div>
  );
}
