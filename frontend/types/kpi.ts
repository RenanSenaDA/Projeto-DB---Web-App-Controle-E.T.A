export type KPIData = {
  id: string;
  label: string;
  value: number | null;
  unit: string | null;
  limit: number | null;
  category: string;
  updated_at: string;
};

export interface KPIsStation {
  kpis: KPIData[];
}

export interface ApiResponse {
  meta: {
    timestamp: string;
    status: string;
  };
  data: {
    [key: string]: KPIsStation;
  };
}
