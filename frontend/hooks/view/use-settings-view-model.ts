import { useState, useEffect, useMemo, useCallback } from "react";
import { toast } from "sonner";
import { defaultHttpClient } from "@/services/http";
import { createLimitsService } from "@/services/limits";
import { createAlarmsService } from "@/services/alarms";
import useApi from "@/hooks/api/use-api";
import type { ApiResponse } from "@/types/kpi";
import { buildCategoryMap } from "@/lib/utils";

/**
 * ViewModel para a página de Configurações.
 * Gerencia a edição de limites de KPIs e o status global de alarmes.
 */
export function useSettingsViewModel(initialData?: ApiResponse | null) {
  // Carrega dados para listar as estações/KPIs
  const { loading, error, data, fetchData } = useApi(initialData);
  
  // Estado local
  const [limits, setLimits] = useState<Record<string, number | null>>({});
  const [saving, setSaving] = useState<string | null>(null); // ID do item sendo salvo
  const [alarmsEnabled, setAlarmsEnabled] = useState<boolean | null>(null);
  const [alarmsLoading, setAlarmsLoading] = useState<boolean>(true);
  const [toggling, setToggling] = useState<boolean>(false);

  // --- Computed properties ---
  
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

  // --- Effects ---

  // Inicializa o estado local de limites com os valores vindos da API
  useEffect(() => {
    if (!data) return;
    const allKPIs = Object.values(data.data ?? {}).flatMap((s) => s.kpis || []);
    const initial: Record<string, number | null> = {};
    allKPIs.forEach((k) => {
      initial[k.id] = k.limit ?? null;
    });
    setLimits(initial);
  }, [data]);

  // Carrega o status inicial dos alarmes globais
  useEffect(() => {
    const loadAlarmsStatus = async () => {
      setAlarmsLoading(true);
      try {
        const svc = createAlarmsService(defaultHttpClient);
        const json = await svc.getStatus();
        setAlarmsEnabled(json.alarms_enabled);
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "Falha ao carregar status dos alarmes";
        toast.error(msg);
        setAlarmsEnabled(null);
      } finally {
        setAlarmsLoading(false);
      }
    };
    loadAlarmsStatus();
  }, []);

  // --- Actions ---

  // Atualiza estado local (controlled input)
  const handleLimitChange = useCallback((id: string, value: string) => {
    const parsed = value === "" ? null : Number(value);
    setLimits((prev) => ({ ...prev, [id]: parsed }));
  }, []);

  // Persiste o limite na API
  const saveLimit = useCallback(async (id: string) => {
    const value = limits[id];
    if (value === null || Number.isNaN(value)) return;
    setSaving(id);
    try {
      const svc = createLimitsService(defaultHttpClient);
      await svc.updateById(id, Number(value));
      await fetchData({ silent: true }); // Recarrega dados sem tela de loading
      toast.success("Limite atualizado com sucesso");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Falha ao atualizar limite";
      toast.error(msg);
    } finally {
      setSaving(null);
    }
  }, [limits, fetchData]);

  // Alterna status global dos alarmes
  const toggleAlarms = useCallback(async () => {
    if (alarmsEnabled === null) return;
    setToggling(true);
    try {
      const svc = createAlarmsService(defaultHttpClient);
      const next = !alarmsEnabled;
      await svc.setStatus(next);
      setAlarmsEnabled(next);
      toast.success(next ? "Alarmes ativados" : "Alarmes desativados");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Falha ao atualizar status dos alarmes";
      toast.error(msg);
    } finally {
      setToggling(false);
    }
  }, [alarmsEnabled]);
  
  const getKPIsForStationAndCategory = (stationKey: string, categoryId: string) => {
     return data?.data?.[stationKey]?.kpis?.filter(k => k.category === categoryId) ?? [];
  };

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
    getKPIsForStationAndCategory
  };
}
