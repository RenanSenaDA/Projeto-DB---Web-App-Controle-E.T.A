import { useState, useEffect, useCallback, useMemo } from "react";
import { toast } from "sonner";
import { createMeasurementsService } from "@/services/measurements";
import { defaultHttpClient } from "@/services/http";

type SeriesMap = Record<
  string,
  { ts: string; value: number; unit?: string | null }[]
>;

export default function useSeries(tags: string[], minutes: number) {
  const [data, setData] = useState<SeriesMap>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const tagsKey = useMemo(() => {
    if (!tags || !tags.length) return "";
    return [...tags].sort().join(",");
  }, [tags]);

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

  useEffect(() => {
    fetchSeries();
  }, [fetchSeries]);

  return { data, loading, error, refresh: fetchSeries };
}
