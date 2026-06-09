import { useState, useEffect, useCallback, useMemo } from "react";
import { toast } from "sonner";
import { defaultHttpClient } from "@/services/http";
import {
  createAlarmHistoryService,
  type AlarmEvent,
  type AlarmLimit,
  type LimitRangeInput,
} from "@/services/alarm-history";

export type StatusFilter = "" | "open" | "acked" | "resolved";

/**
 * View-Model da tela de Alarmes: histórico (com reconhecimento) + faixas (min/max).
 */
export function useAlarmsViewModel() {
  const svc = useMemo(() => createAlarmHistoryService(defaultHttpClient), []);

  // ---------------- Histórico ----------------
  const [events, setEvents] = useState<AlarmEvent[]>([]);
  const [loadingEvents, setLoadingEvents] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("");
  const [acking, setAcking] = useState<number | null>(null);

  const loadEvents = useCallback(
    async (status: StatusFilter) => {
      setLoadingEvents(true);
      try {
        const data = await svc.getEvents(status || undefined, 200);
        setEvents(data);
      } catch (e) {
        toast.error(e instanceof Error ? e.message : "Falha ao carregar histórico");
      } finally {
        setLoadingEvents(false);
      }
    },
    [svc]
  );

  const ackEvent = useCallback(
    async (id: number) => {
      setAcking(id);
      try {
        await svc.ackEvent(id);
        toast.success("Alarme reconhecido");
        await loadEvents(statusFilter);
      } catch (e) {
        toast.error(e instanceof Error ? e.message : "Falha ao reconhecer alarme");
      } finally {
        setAcking(null);
      }
    },
    [svc, loadEvents, statusFilter]
  );

  const changeFilter = useCallback(
    (f: StatusFilter) => {
      setStatusFilter(f);
      void loadEvents(f);
    },
    [loadEvents]
  );

  useEffect(() => {
    void loadEvents("");
  }, [loadEvents]);

  // ---------------- Faixas (limites min/max) ----------------
  const [limits, setLimits] = useState<AlarmLimit[]>([]);
  const [loadingLimits, setLoadingLimits] = useState<boolean>(true);
  const [drafts, setDrafts] = useState<Record<string, LimitRangeInput>>({});
  const [savingTag, setSavingTag] = useState<string | null>(null);

  const loadLimits = useCallback(async () => {
    setLoadingLimits(true);
    try {
      const data = await svc.getLimits();
      setLimits(data);
      const d: Record<string, LimitRangeInput> = {};
      data.forEach((l) => {
        d[l.tag] = { limite_min: l.limite_min, limite_max: l.limite_max, label: l.label };
      });
      setDrafts(d);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Falha ao carregar faixas");
    } finally {
      setLoadingLimits(false);
    }
  }, [svc]);

  useEffect(() => {
    void loadLimits();
  }, [loadLimits]);

  const setDraft = useCallback(
    (tag: string, field: keyof LimitRangeInput, value: string) => {
      setDrafts((prev) => {
        const cur = prev[tag] ?? {};
        let v: number | string | null;
        if (field === "label") {
          v = value === "" ? null : value;
        } else {
          const n = Number(value);
          v = value === "" || Number.isNaN(n) ? null : n;
        }
        return { ...prev, [tag]: { ...cur, [field]: v } as LimitRangeInput };
      });
    },
    []
  );

  const saveRange = useCallback(
    async (tag: string) => {
      const rg = drafts[tag];
      if (!rg) return;
      setSavingTag(tag);
      try {
        await svc.putLimits({ [tag]: rg });
        toast.success("Faixa salva");
        await loadLimits();
      } catch (e) {
        toast.error(e instanceof Error ? e.message : "Falha ao salvar faixa");
      } finally {
        setSavingTag(null);
      }
    },
    [drafts, svc, loadLimits]
  );

  return {
    // histórico
    events,
    loadingEvents,
    statusFilter,
    acking,
    ackEvent,
    changeFilter,
    // faixas
    limits,
    loadingLimits,
    drafts,
    savingTag,
    setDraft,
    saveRange,
  };
}
