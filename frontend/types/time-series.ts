/**
 * Representa um único ponto de medição retornado pela API.
 * Corresponde ao dicionário Python: { "ts": datetime, "value": float, "unit": str }
 */
export interface SeriesPoint {
  /** Timestamp ISO string (ex: "2025-12-29T14:30:00.000Z") */
  ts: string;
  /** Valor numérico da medição */
  value: number;
  /** Unidade de medida (opcional, pode vir null do banco) */
  unit?: string | null;
}

/**
 * Mapa de Séries Temporais retornado pelo endpoint /measurements/series.
 * A chave é a TAG do sensor e o valor é a lista de pontos.
 * * Corresponde ao Python: Dict[str, List[Dict]]
 */
export type SeriesMap = Record<string, SeriesPoint[]>;

/**
 * Representa um ponto de dados formatado especificamente para gráficos (Recharts/Apex).
 * Geralmente criado no frontend após processar o SeriesPoint.
 */
export interface ChartDataPoint {
  /** Timestamp original para ordenação ou tooltip detalhado */
  ts: string;
  /** Label formatada para o Eixo X (ex: "14:30") */
  label: string;
  /** Valor para o Eixo Y */
  value: number;
}