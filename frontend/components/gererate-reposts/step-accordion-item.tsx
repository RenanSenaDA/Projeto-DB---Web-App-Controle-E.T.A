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

const STEPS_CONFIG: Record<string, { label: string; icon: LucideIcon }> = {
  eta: { label: "ETA", icon: Factory },
  ultrafiltracao: { label: "Ultrafiltração", icon: Waves },
  carvao: { label: "Filtro de Carvão", icon: Filter },
};

interface StepAccordionItemProps {
  systemKey: string;
  kpis: KPIData[];
  selectedKpis: string[];
  onToggleSystemAll: (kpis: KPIData[]) => void;
  onToggleKpi: (id: string) => void;
}

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
      className={cn(
        "bg-white rounded-xl border border-slate-200 shadow-sm mb-4 overflow-hidden",
        "data-[state=open]:border-blue-200 data-[state=open]:shadow-md"
      )}
    >
      <AccordionTrigger className="flex px-4 py-4 hover:bg-slate-50/50">
        <div className="flex items-center gap-3 text-left">
          <div className="p-2 rounded-lg bg-primary/10 border border-primary">
            <Icon className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-800 text-sm sm:text-base">
              {config.label}
            </h3>
            <p className="text-xs text-slate-500 font-normal">
              {selectedCount} de {kpis.length} selecionados
            </p>
          </div>
        </div>
      </AccordionTrigger>

      <AccordionContent className="px-4 pb-4 pt-0 border-t border-slate-100">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onToggleSystemAll(kpis);
          }}
          className="text-xs font-medium text-secondary hover:underline px-2 mr-2 pt-4 hidden sm:block"
        >
          {allSelected ? "Desmarcar todos" : "Selecionar todos"}
        </button>

        <div className="pt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
          {kpis.map((kpi) => {
            const isSelected = selectedKpis.includes(kpi.id);
            return (
              <div
                key={kpi.id}
                onClick={() => onToggleKpi(kpi.id)}
                className={cn(
                  "flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all hover:bg-slate-50",
                  isSelected
                    ? "border-secondary bg-slate-50/50"
                    : "border-slate-200"
                )}
              >
                <div
                  className={cn(
                    "h-5 w-5 rounded border flex items-center justify-center",
                    isSelected
                      ? "bg-secondary border-secondary"
                      : "bg-white border-slate-300"
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
                      isSelected ? "text-secondary" : "text-slate-600"
                    )}
                  >
                    {kpi.label}
                  </span>
                  <span className="text-[10px] text-slate-400 uppercase">
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
