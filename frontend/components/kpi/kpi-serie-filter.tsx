"use client";

import { Badge } from "@/ui/badge";
import { Button } from "@/ui/button";
import { Filter, X } from "lucide-react";
import type { KPIData } from "@/types/kpi";

/**
 * Propriedades do Filtro de Séries de KPI.
 */
interface KpiFilterProps {
  /** Lista completa de KPIs disponíveis */
  allKpis: KPIData[];
  /** Lista de IDs de KPIs selecionados para filtragem */
  selectedFilters: string[];
  /** Função para alternar o filtro de uma KPI */
  toggleFilter: (kpiId: string) => void;
  /** Função para limpar todos os filtros */
  clearFilters: () => void;
}

/**
 * Componente para filtrar visualização de séries temporais.
 * Exibe badges interativos para cada KPI disponível e botão de limpeza.
 * 
 * @component
 */
export default function KpiSeriesFilter({
  allKpis,
  selectedFilters,
  toggleFilter,
  clearFilters,
}: KpiFilterProps) {
  return (
    <div className="flex flex-col gap-4 bg-card rounded-lg border p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-primary" />
          <h4 className="text-sm font-medium text-foreground">
            Filtrar Indicadores
          </h4>
          <span className="text-xs text-muted-foreground ml-1">
            ({selectedFilters.length} selecionados)
          </span>
        </div>
        
        {selectedFilters.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearFilters}
            className="h-8 px-2 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
          >
            Limpar filtros
            <X className="w-3 h-3 ml-2" />
          </Button>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        {allKpis.map((kpi) => {
          const isSelected = selectedFilters.includes(kpi.id);
          
          return (
            <Badge
              key={kpi.id}
              variant={isSelected ? "default" : "outline"}
              className={`
                cursor-pointer transition-all py-1.5 px-3 text-sm font-normal
                ${isSelected 
                  ? "hover:bg-primary/90 shadow-sm" 
                  : "hover:bg-accent hover:text-accent-foreground text-muted-foreground border-dashed"
                }
              `}
              onClick={() => toggleFilter(kpi.id)}
            >
              {kpi.label}
            </Badge>
          );
        })}
      </div>
    </div>
  );
}
