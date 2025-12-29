import { useState, useEffect, useCallback, useMemo } from "react";
import { toast } from "sonner";
import { createMeasurementsService } from "@/services/measurements";
import { defaultHttpClient } from "@/services/http";
import type { SeriesMap } from "@/types/time-series";

/**
 * Hook para buscar séries temporais históricas.
 * Otimizado para evitar chamadas desnecessárias (só busca se houver tags).
 *
 * @param tags - Lista de tags (sensores) para buscar dados (ex: ["ete/nivel", "ete/ph"])
 * @param minutes - Janela de tempo em minutos para trás (ex: 60 = última hora)
 */
export default function useSeries(tags: string[], minutes: number) {
  const [data, setData] = useState<SeriesMap>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Memoiza a chave de dependência para evitar loops de efeito se o array mudar de referência
  const tagsKey = useMemo(() => {
    if (!tags || !tags.length) return "";
    return [...tags].sort().join(",");
  }, [tags]);

  /**
   * Executa a busca na API /measurements/series
   */
  const fetchSeries = useCallback(async () => {
    const tagList = tagsKey ? tagsKey.split(",") : [];
    if (!tagList.length) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const svc = createMeasurementsService(defaultHttpClient);
      const json = await svc.getSeries(tagList, minutes);
      setData(json as SeriesMap);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Falha ao carregar séries";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, [tagsKey, minutes]);

  // Recarrega sempre que as tags ou o intervalo mudarem
  useEffect(() => {
    fetchSeries();
  }, [fetchSeries]);

  return { data, loading, error, refresh: fetchSeries };
}
