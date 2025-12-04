export type KPICategory =
  | "operacional"
  | "qualidade_da_agua"
  | "limpeza_e_manutencao"
  | "integridade_e_alarme"
  | "default";

export type KPIStatusOperation =
  | "operação"
  | "parado"
  | "retrolavagem"
  | "sanitização";

export type KPIHistoryPoint = {
  date: string;
  timestamp: string;
  value: number;
};

export type KPIData = {
  id: string;
  label: string;
  value: number | null;
  unit: string | null;
  status_operation?: KPIStatusOperation | null;
  limit?: number | null;
  category: KPICategory;
  updated_at: string;
  history?: KPIHistoryPoint[];
};

export interface stationData {
  kpis: KPIData[];
}

export interface DashboardResponse {
  meta: {
    timestamp: string;
    status: string;
  };
  data: {
    eta: stationData;
    ultrafiltracao: stationData;
    carvao: stationData;
  };
}

export const SECTIONS = {
  operacional: {
    color: "bg-blue-600",
    title: "Operacional",
  },
  qualidade_da_agua: {
    color: "bg-emerald-600",
    title: "Qualidade da Água",
  },
  limpeza_e_manutencao: {
    color: "bg-amber-500",
    title: "Limpeza e Manutenção",
  },
  integridade_e_alarme: {
    color: "bg-red-500",
    title: "Integridade e Alarme",
  },
  default: {
    color: "bg-slate-400",
    title: "Seção",
  },
} as const;
