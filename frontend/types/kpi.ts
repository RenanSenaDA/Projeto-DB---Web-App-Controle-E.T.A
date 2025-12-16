/**
 * Definição dos dados de uma KPI (Indicador Chave de Performance).
 */
export type KPIData = {
  id: string;         // Identificador único interno
  label: string;      // Nome legível da KPI
  value: number | null; // Valor atual da medição
  unit: string | null;  // Unidade de medida (ex: mg/L, pH)
  limit: number | null; // Limite operacional configurado
  category: string;     // Categoria (ex: quimico, fisico)
  updated_at: string;   // Timestamp da última atualização
};

/**
 * Estrutura de dados de uma Estação.
 * Contém uma lista de KPIs associadas.
 */
export interface KPIsStation {
  kpis: KPIData[];
}

/**
 * Resposta padrão da API de Dashboard.
 * Estrutura hierárquica: Estação -> KPIs.
 */
export interface ApiResponse {
  meta: {
    timestamp: string; // Momento da geração dos dados no servidor
    status: string;    // Status da resposta
  };
  data: {
    [key: string]: KPIsStation; // Mapa de chaves de estação para seus dados
  };
}
