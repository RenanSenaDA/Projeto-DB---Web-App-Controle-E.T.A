"use client";

import { useState, useEffect } from "react";

import { Tabs, TabsContent } from "@/ui/tabs";

import { Button } from "@/ui/button";

import PageHeader from "@/components/header-page";
import Loading from "@/components/feedback/loading";
import SectionLabel from "@/components/label-section";
import TabsListStation from "@/components/tabs-list-station";

import { defaultHttpClient } from "@/services/http";
import { createLimitsService } from "@/services/limits";

import useApi from "@/hooks/use-api";
import { SECTIONS, type KPICategory, type KPIData } from "@/types/kpi";

export default function SettingsPage() {
  const { loading, error, data, fetchData } = useApi();
  const [limits, setLimits] = useState<Record<string, number | null>>({});
  const [saving, setSaving] = useState<string | null>(null);

  useEffect(() => {
    if (!data) return;

    const allKPIs = [
      ...data.data.eta.kpis,
      ...data.data.ultrafiltracao.kpis,
      ...data.data.carvao.kpis,
    ];

    const initial: Record<string, number | null> = {};
    allKPIs.forEach((k) => {
      initial[k.id] = k.limit ?? null;
    });

    setLimits(initial);
  }, [data]);

  const handleChange = (id: string, value: string) => {
    const parsed = value === "" ? null : Number(value);
    setLimits((prev) => ({ ...prev, [id]: parsed }));
  };

  const saveLimit = async (id: string) => {
    const value = limits[id];
    if (value === null || Number.isNaN(value)) return;
    setSaving(id);
    try {
      const svc = createLimitsService(defaultHttpClient);
      await svc.updateById(id, Number(value));
      await fetchData({ silent: true });
    } finally {
      setSaving(null);
    }
  };

  if (loading) return <Loading />;
  if (error) return <p>Erro ao carregar</p>;
  if (!data) return null;

  const stations = {
    eta: data.data.eta.kpis,
    ultrafiltracao: data.data.ultrafiltracao.kpis,
    carvao: data.data.carvao.kpis,
  };

  return (
    <div className="container mx-auto p-6">
      <PageHeader
        title="Configurações"
        subtitle="Definição de limites máximos para KPIs"
      />

      <Tabs defaultValue="eta" className="w-full">
        <TabsListStation />

        {Object.entries(stations).map(([key, kpis]) => (
          <TabsContent key={key} value={key}>
            {(
              Object.entries(SECTIONS) as [
                KPICategory,
                (typeof SECTIONS)[keyof typeof SECTIONS]
              ][]
            ).map(([category, config]) => {
              const sectionItems = (kpis as KPIData[]).filter(
                (k) => k.category === category
              );

              if (!sectionItems.length) return null;

              return (
                <div key={category} className="mb-10">
                  <SectionLabel title={config.title} color={config.color} />

                  <div className="space-y-4">
                    {sectionItems.map((kpi) => (
                      <div
                        key={kpi.id}
                        className="p-4 bg-white shadow-sm rounded-lg border flex flex-col gap-2"
                      >
                        <div className="flex flex-col lg:flex-row justify-between lg:items-center">
                          <div className="mb-2 lg:mb-0">
                            <p className="font-medium">{kpi.label}</p>
                            <p className="text-sm text-slate-500">
                              Valor atual: {kpi.value} {kpi.unit || ""}
                            </p>
                          </div>

                          <div className="flex items-center gap-3 px-0">
                            <input
                              type="number"
                              className="border rounded px-3 py-1 w-full lg:w-28"
                              placeholder="Limite"
                              value={limits[kpi.id] ?? ""}
                              onChange={(e) =>
                                handleChange(kpi.id, e.target.value)
                              }
                            />

                            <Button
                              onClick={() => saveLimit(kpi.id)}
                              disabled={
                                limits[kpi.id] === null || saving === kpi.id
                              }
                              className="px-3 py-1 bg-[#00B4F0] text-white rounded hover:bg-[#00283F] disabled:bg-slate-200 disabled:text-slate-400"
                            >
                              {saving === kpi.id ? "Salvando..." : "Salvar"}
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
