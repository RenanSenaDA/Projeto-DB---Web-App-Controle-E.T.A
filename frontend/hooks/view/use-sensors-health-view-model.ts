import { useState, useEffect, useCallback, useMemo } from "react";
import { toast } from "sonner";
import { defaultHttpClient } from "@/services/http";
import { createSensorsService, type SensorHealth } from "@/services/sensors";

/** View-Model do painel de saúde dos sensores (com auto-refresh a cada 30s). */
export function useSensorsHealthViewModel() {
  const svc = useMemo(() => createSensorsService(defaultHttpClient), []);
  const [items, setItems] = useState<SensorHealth[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const load = useCallback(async () => {
    try {
      const data = await svc.getHealth();
      setItems(data);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Falha ao carregar saúde dos sensores");
    } finally {
      setLoading(false);
    }
  }, [svc]);

  useEffect(() => {
    void load();
    const t = setInterval(() => void load(), 30000);
    return () => clearInterval(t);
  }, [load]);

  return { items, loading, reload: load };
}
