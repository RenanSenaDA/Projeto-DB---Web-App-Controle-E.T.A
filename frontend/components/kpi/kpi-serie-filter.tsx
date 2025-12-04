"use client";

import type { KPIData } from "@/types/kpi";
import { Badge } from "@/ui/badge";

interface KpiFilterProps {
  allKpis: KPIData[];
  selectedFilters: string[];
  toggleFilter: (kpiId: string) => void;
  clearFilters: () => void;
}

export default function KpiSeriesFilter({
  allKpis,
  selectedFilters,
  toggleFilter,
  clearFilters,
}: KpiFilterProps) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <h4 className="text-sm font-semibold text-[#00283F]">Filtro de KPIs</h4>
        <div className="flex items-center gap-2">
          <Badge variant="secondary">
            Selecionados: {selectedFilters.length}
          </Badge>
          {selectedFilters.length > 0 && (
            <button
              className="px-3 py-1 text-sm font-medium text-white bg-[#00B4F0] rounded hover:bg-[#00283F] transition"
              onClick={clearFilters}
            >
              Limpar
            </button>
          )}
        </div>
      </div>

      <div className="flex flex-wrap gap-3 max-h-48 overflow-y-auto border rounded p-3 bg-white shadow-sm">
        {allKpis.map((kpi) => (
          <label
            key={kpi.id}
            className={`flex items-center gap-2 px-2 py-1 rounded cursor-pointer transition ${
              selectedFilters.includes(kpi.id)
                ? "bg-[#00B4F0]/10 border border-[#00B4F0]"
                : "hover:bg-slate-100"
            }`}
          >
            <input
              type="checkbox"
              className="text-[#00B4F0]"
              checked={selectedFilters.includes(kpi.id)}
              onChange={() => toggleFilter(kpi.id)}
            />
            <span className="text-sm">
              {kpi.label ? kpi.label[0].toUpperCase() + kpi.label.slice(1) : ""}
            </span>
          </label>
        ))}
      </div>
    </div>
  );
}
