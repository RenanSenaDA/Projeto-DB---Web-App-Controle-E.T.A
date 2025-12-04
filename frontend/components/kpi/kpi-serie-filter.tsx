"use client";

import type { KPIData } from "@/types/kpi";

interface KpiFilterProps {
  allKpis: KPIData[];
  selectedFilters: string[];
  toggleFilter: (kpiId: string) => void;
  clearFilters: () => void; // nova prop
}

export default function KpiSeriesFilter({
  allKpis,
  selectedFilters,
  toggleFilter,
  clearFilters,
}: KpiFilterProps) {
  return (
    <div className="flex flex-col gap-2">
      {/* Botão de limpar filtros */}
      {selectedFilters.length > 0 && (
        <button
          className="self-start px-3 py-1 text-sm font-medium text-white bg-[#00B4F0] rounded hover:bg-[#00283F] transition"
          onClick={clearFilters}
        >
          Limpar filtros
        </button>
      )}

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
            <span className="text-sm">{kpi.label}</span>
          </label>
        ))}
      </div>
    </div>
  );
}
