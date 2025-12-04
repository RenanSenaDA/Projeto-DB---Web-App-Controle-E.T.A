import { useState, useEffect, useCallback } from "react";
import { MOCK_API_RESPONSE } from "@/lib/mock-data";
import type { DashboardResponse, KPICategory } from "@/types/kpi";

export default function useApi() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Simula latência de rede (1.5 segundos)
      await new Promise((resolve) => setTimeout(resolve, 1500));
      
      // Simula uma falha aleatória (descomente para testar erro)
      // if (Math.random() < 0.1) throw new Error("Falha na comunicação com o CLP.");

      // Atualiza o timestamp para simular dados em tempo real
      const freshData: DashboardResponse = {
        ...MOCK_API_RESPONSE,
        meta: {
          ...MOCK_API_RESPONSE.meta,
          timestamp: new Date().toLocaleTimeString("pt-BR"),
        },
        // Aqui você poderia adicionar lógica para variar levemente os valores
        // para parecer "vivo" (ex: value + Math.random())
      };

      setData(freshData);
    } catch (err) {
      console.error("Erro na API:", err);
      setError("Não foi possível conectar ao servidor de dados.");
    } finally {
      setLoading(false);
    }
  }, []);

  // Efeito de montagem e polling
  useEffect(() => {
    fetchData();
    
    // Atualiza automaticamente a cada 60 segundos
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, [fetchData]);

  /**
   * Utilitário para filtrar KPIs na UI de forma limpa
   */
  const getKPIs = useCallback((
    stations: "eta" | "ultrafiltracao" | "carvao",
    category?: KPICategory
  ) => {
    if (!data) return [];
    
    const stationsData = data.data[stations];
    if (!stationsData) return [];

    const kpis = stationsData.kpis;
    
    if (!category) return kpis;

    console.log("API RAW:", data)
    
    return kpis.filter((kpi) => kpi.category === category);
  }, [data]);

  return {
    data,
    loading,
    error,
    fetchData,
    getKPIs,
  };
}