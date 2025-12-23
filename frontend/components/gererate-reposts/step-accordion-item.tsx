import {
  CheckCircle2,
  CheckSquare,
  Factory,
  Filter,
  Waves,
  type LucideIcon,
} from "lucide-react";

import {
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/ui/accordion";

import { cn } from "@/lib/utils";
import type { KPIData } from "@/types/kpi";
import { formatCategory } from "@/lib/format";

/**
 * Configuração visual para cada etapa/sistema do processo.
 * Mapeia chaves de sistema para rótulos legíveis e ícones.
 */
const STEPS_CONFIG: Record<string, { label: string; icon: LucideIcon }> = {
  eta: { label: "ETA", icon: Factory },
  ultrafiltracao: { label: "Ultrafiltração", icon: Waves },
  carvao: { label: "Filtro de Carvão", icon: Filter },
};

/**
 * Propriedades do Item de Acordeão para seleção de KPIs.
 */
interface StepAccordionItemProps {
  /** Chave identificadora do sistema (ex: eta, ultrafiltracao) */
  systemKey: string;
  /** Lista de KPIs disponíveis neste sistema */
  kpis: KPIData[];
  /** IDs das KPIs atualmente selecionadas */
  selectedKpis: string[];
  /** Callback para selecionar/desmarcar todas as KPIs do sistema */
  onToggleSystemAll: (kpis: KPIData[]) => void;
  /** Callback para alternar a seleção de uma KPI específica */
  onToggleKpi: (id: string) => void;
}

/**
 * Componente de item de acordeão para um grupo de KPIs.
 * Exibe o status de seleção e permite marcar métricas individualmente ou em grupo.
 *
 * @component
 */
export default function StepAccordionItem({
  systemKey,
  kpis,
  selectedKpis,
  onToggleSystemAll,
  onToggleKpi,
}: StepAccordionItemProps) {
  const config = STEPS_CONFIG[systemKey] || {
    label: systemKey,
    icon: CheckSquare,
  };
  const Icon = config.icon;

  const selectedCount = kpis.filter((k) => selectedKpis.includes(k.id)).length;
  const allSelected = selectedCount === kpis.length && kpis.length > 0;

  return (
    <AccordionItem
      value={systemKey}
      className="bg-card rounded-xl border shadow-sm mb-4 overflow-hidden"
    >
      <AccordionTrigger className="flex px-4 py-4 hover:bg-muted/50">
        <div className="flex items-center gap-3 text-left">
          <div className="p-2 rounded-lg bg-primary/10 border border-primary">
            <Icon className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground text-sm sm:text-base">
              {config.label}
            </h3>
            <p className="text-xs text-muted-foreground font-normal">
              {selectedCount} de {kpis.length} selecionados
            </p>
          </div>
        </div>
      </AccordionTrigger>

      <AccordionContent className="px-4 pb-4 pt-0 border-t border-border dark:border-white/10">
        <div className="flex items-center justify-end py-3 mb-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggleSystemAll(kpis);
            }}
            className="group flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all hover:bg-secondary/10 active:scale-95 border border-transparent hover:border-secondary/20"
          >
            <span
              className={cn(
                "text-secondary dark:text-foreground transition-colors"
              )}
            >
              {allSelected ? "Desmarcar todos" : "Selecionar todos"}
            </span>
            <div
              className={cn(
                "h-4 w-4 rounded border flex items-center justify-center transition-colors",
                allSelected
                  ? "bg-secondary border-secondary text-secondary-foreground"
                  : "border-muted-foreground/30 bg-background group-hover:border-secondary"
              )}
            >
              {allSelected && <CheckCircle2 className="h-3 w-3" />}
            </div>
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {kpis.map((kpi) => {
            const isSelected = selectedKpis.includes(kpi.id);
            return (
              <div
                key={kpi.id}
                onClick={() => onToggleKpi(kpi.id)}
                className={cn(
                  "flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all hover:bg-muted/50",
                  isSelected ? "border-secondary bg-muted/50" : "border-border"
                )}
              >
                <div
                  className={cn(
                    "h-5 w-5 rounded border flex items-center justify-center",
                    isSelected
                      ? "bg-secondary border-secondary"
                      : "bg-background border-input"
                  )}
                >
                  {isSelected && (
                    <CheckCircle2 className="h-3.5 w-3.5 text-white" />
                  )}
                </div>

                <div className="flex flex-col min-w-0">
                  <span
                    className={cn(
                      "text-sm font-medium truncate",
                      isSelected ? "text-secondary dark:text-foreground" : "text-foreground"
                    )}
                  >
                    {kpi.label}
                  </span>
                  <span className="text-[10px] text-muted-foreground uppercase">
                    {formatCategory(kpi.category)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </AccordionContent>
    </AccordionItem>
  );
}
