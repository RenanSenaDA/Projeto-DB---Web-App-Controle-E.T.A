import { useState, useEffect, useMemo, useCallback } from "react";
import { toast } from "sonner";
import { defaultHttpClient } from "@/services/http";
import { createLimitsService } from "@/services/limits";
import { createAlarmsService } from "@/services/alarms";
import useApi from "@/hooks/api/use-api";
import type { ApiResponse } from "@/types/kpi";
import { buildCategoryMap } from "@/lib/utils";

type AlarmStatusResponse = {
  alarms_enabled: boolean;
};

function extractTagFromLabel(label: string): string {
  // label vem como "bombeamento/vazao (m³/h)" ou "pressao/linha1 (bar)"
  // ou às vezes só "qualidade/ph"
  const raw = (label || "").trim();
  const idx = raw.indexOf(" (");
  return (idx >= 0 ? raw.slice(0, idx) : raw).trim();
}

/**
 * ViewModel para a página de Configurações de Limites.
 * Gerencia a edição de limites de KPIs e o status global de alarmes.
 */
export function useLimitsViewModel(initialData?: ApiResponse | null) {
  const { loading, error, data, fetchData } = useApi(initialData);

  const [limits, setLimits] = useState<Record<string, number | null>>({});
  const [saving, setSaving] = useState<string | null>(null);

  // null = ainda não carregou / erro
  const [alarmsEnabled, setAlarmsEnabled] = useState<boolean | null>(null);
  const [alarmsLoading, setAlarmsLoading] = useState<boolean>(true);
  const [toggling, setToggling] = useState<boolean>(false);

  const limitsSvc = useMemo(() => createLimitsService(defaultHttpClient), []);
  const alarmsSvc = useMemo(() => createAlarmsService(defaultHttpClient), []);

  const stationKeys = useMemo(() => {
    return Object.keys(data?.data ?? {}).filter(
      (key) => (data?.data?.[key]?.kpis?.length ?? 0) > 0
    );
  }, [data]);

  const stationsList = useMemo(() => {
    return stationKeys.map((key) => ({ key, label: key.toUpperCase() }));
  }, [stationKeys]);

  const categoryMap = useMemo(() => {
    return data ? buildCategoryMap(data) : {};
  }, [data]);

  // Inicializa limites no estado local
  useEffect(() => {
    if (!data) return;
    const allKPIs = Object.values(data.data ?? {}).flatMap((s) => s.kpis || []);
    const initial: Record<string, number | null> = {};

    allKPIs.forEach((k) => {
      // Guardamos por k.id (chave do input / render), porque a tela usa k.id
      initial[k.id] = k.limit ?? null;
    });

    setLimits(initial);
  }, [data]);

  // Carrega status dos alarmes
  const loadAlarmsStatus = useCallback(async () => {
    setAlarmsLoading(true);
    try {
      const json = (await alarmsSvc.getStatus()) as AlarmStatusResponse;
      setAlarmsEnabled(Boolean(json?.alarms_enabled));
    } catch (e: unknown) {
      const msg =
        e instanceof Error ? e.message : "Falha ao carregar status dos alarmes";
      toast.error(msg);
      setAlarmsEnabled(null);
    } finally {
      setAlarmsLoading(false);
    }
  }, [alarmsSvc]);

  useEffect(() => {
    loadAlarmsStatus();
  }, [loadAlarmsStatus]);

  const handleLimitChange = useCallback((id: string, value: string) => {
    const parsed = value === "" ? null : Number(value);
    setLimits((prev) => ({ ...prev, [id]: parsed }));
  }, []);

  const saveLimit = useCallback(
    async (id: string) => {
      const value = limits[id];
      if (value === null || Number.isNaN(value)) return;

      // Precisa converter o KPI "id" para TAG real do banco.
      // Pegamos o KPI pela lista e extraímos a tag do label.
      const allKPIs = Object.values(data?.data ?? {}).flatMap((s) => s.kpis || []);
      const kpi = allKPIs.find((k) => k.id === id);

      if (!kpi) {
        toast.error("KPI não encontrado para salvar limite");
        return;
      }

      const tag = extractTagFromLabel(kpi.label);

      setSaving(id);
      try {
        await limitsSvc.updateByTag(tag, Number(value));
        await fetchData({ silent: true });
        toast.success("Limite atualizado com sucesso");
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "Falha ao atualizar limite";
        toast.error(msg);
      } finally {
        setSaving(null);
      }
    },
    [limits, fetchData, limitsSvc, data]
  );

  const toggleAlarms = useCallback(async () => {
    // evita clique durante carregamento/toggle
    if (alarmsLoading || toggling) return;
    if (alarmsEnabled === null) return;

    const next = !alarmsEnabled;

    setToggling(true);
    try {
      // PUT retorna { ok: true }, então sincronizamos via GET em seguida
      await alarmsSvc.setStatus(next);

      // Atualiza UI imediatamente (feedback rápido)
      setAlarmsEnabled(next);
      toast.success(next ? "Alarmes ativados" : "Alarmes desativados");

      // Confirma com o backend (fonte da verdade)
      await loadAlarmsStatus();
    } catch (e: unknown) {
      const msg =
        e instanceof Error ? e.message : "Falha ao atualizar status dos alarmes";
      toast.error(msg);

      // Recarrega status para não deixar UI fora de sincronia
      await loadAlarmsStatus().catch(() => {});
    } finally {
      setToggling(false);
    }
  }, [alarmsEnabled, alarmsLoading, toggling, alarmsSvc, loadAlarmsStatus]);

  const getKPIsForStationAndCategory = useCallback(
    (stationKey: string, categoryId: string) => {
      return (
        data?.data?.[stationKey]?.kpis?.filter((k) => k.category === categoryId) ??
        []
      );
    },
    [data]
  );

  return {
    loading,
    error,
    data,
    stationKeys,
    stationsList,
    categoryMap,
    limits,
    saving,
    alarmsEnabled,
    alarmsLoading,
    toggling,
    handleLimitChange,
    saveLimit,
    toggleAlarms,
    getKPIsForStationAndCategory,
  };
}
