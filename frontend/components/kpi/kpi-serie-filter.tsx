"use client";

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
 * Exibe checkboxes para cada KPI disponível e botão de limpeza.
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
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <h4 className="text-sm font-semibold text-secondary-foreground">Filtro de KPIs</h4>
        <div className="flex items-center gap-2">
          {selectedFilters.length > 0 && (
            <button
              className="px-3 py-1 text-sm font-medium text-white bg-primary rounded hover:bg-secondary transition"
              onClick={clearFilters}
            >
              Limpar
            </button>
          )}
        </div>
      </div>

      <div className="flex flex-wrap gap-3 max-h-48 overflow-y-auto border rounded p-3 bg-card shadow-sm">
        {allKpis.map((kpi) => (
          <label
            key={kpi.id}
            className={`flex items-center gap-2 px-2 py-1 rounded cursor-pointer transition ${
              selectedFilters.includes(kpi.id)
                ? "bg-primary/10 border border-primary"
                : "hover:bg-muted"
            }`}
          >
            <input
              type="checkbox"
              className="text-primary"
              checked={selectedFilters.includes(kpi.id)}
              onChange={() => toggleFilter(kpi.id)}
            />
            <span className="text-sm">{kpi.label}</span>
          </label>
        ))}
      </div>
    </div>
  );
}
