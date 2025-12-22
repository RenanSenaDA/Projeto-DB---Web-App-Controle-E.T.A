"use client";

import { Tabs, TabsContent } from "@/ui/tabs";
import { Button } from "@/ui/button";
import { Input } from "@/ui/input";

import PageHeader from "@/components/header-page";
import Loading from "@/components/feedback/loading";
import SectionLabel from "@/components/label-section";
import TabsListStation from "@/components/tabs-list-station";

import type { ApiResponse } from "@/types/kpi";
import { formatValue } from "@/lib/format";
import { cn } from "@/lib/utils";
import { useSettingsViewModel } from "@/hooks/view/use-settings-view-model";

interface SettingsClientProps {
  initialData?: ApiResponse | null;
}

export default function SettingsClient({ initialData }: SettingsClientProps) {
  const {
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
  } = useSettingsViewModel(initialData);

  if (loading) return <Loading />;
  if (error) return <p className="text-red-500 p-6">Erro ao carregar dados.</p>;
  if (!data) return null;

  // Converte (string do input) -> número para comparar
  const parseForCompare = (raw: string): number | null => {
    const v = (raw ?? "").trim();
    if (!v) return null;
    const n = Number(v.replace(",", "."));
    if (Number.isNaN(n)) return null;
    return n;
  };

  return (
    <div className="container mx-auto p-6">
      <PageHeader
        title="Configurações"
        subtitle="Definição de limites máximos e controle global de alarmes"
      >
        <div className="flex items-center gap-4 bg-white p-2 rounded-lg border shadow-sm">
          <div className="flex flex-col items-end mr-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Sistema de Alarmes
            </span>
            <span
              className={cn(
                "text-sm font-bold",
                alarmsEnabled ? "text-emerald-600" : "text-rose-600"
              )}
            >
              {alarmsLoading ? "..." : alarmsEnabled ? "ATIVADO" : "DESATIVADO"}
            </span>
          </div>
          <Button
            onClick={toggleAlarms}
            disabled={alarmsLoading || toggling || alarmsEnabled === null}
            size="sm"
            className={cn(
              "text-white min-w-[100px]",
              alarmsEnabled
                ? "bg-rose-600 hover:bg-rose-700"
                : "bg-emerald-600 hover:bg-emerald-700"
            )}
          >
            {toggling ? "..." : alarmsEnabled ? "Desativar" : "Ativar"}
          </Button>
        </div>
      </PageHeader>

      <Tabs defaultValue={stationKeys[0] ?? ""} className="w-full">
        <TabsListStation stations={stationsList} />

        {stationKeys.map((key) => (
          <TabsContent key={key} value={key}>
            {Object.entries(categoryMap).map(([category, config]) => {
              const sectionItems = getKPIsForStationAndCategory(key, category);
              if (!sectionItems.length) return null;

              return (
                <div key={category} className="mb-10">
                  <SectionLabel title={config.title} color={config.color} />
                  <div className="space-y-4">
                    {sectionItems.map((kpi) => {
                      const raw = limits[kpi.id] ?? "";
                      const parsed = parseForCompare(raw);
                      const current = kpi.limit ?? null;

                      const unchanged =
                        parsed === null
                          ? current === null
                          : current !== null && Number(parsed) === Number(current);

                      const disableSave = saving === kpi.id || unchanged;

                      return (
                        <div
                          key={kpi.id}
                          className="p-4 bg-white shadow-sm rounded-lg border flex flex-col gap-2"
                        >
                          <div className="flex flex-col lg:flex-row justify-between lg:items-center">
                            <div className="mb-2 lg:mb-0">
                              <p className="font-medium">{kpi.label}</p>
                              <p className="text-sm text-slate-500">
                                Valor atual: {formatValue(kpi.value)}{" "}
                                {kpi.unit || ""}
                              </p>
                            </div>

                            <div className="flex items-center gap-3 px-0">
                              <Input
                                type="text"
                                inputMode="decimal"
                                className="w-full lg:w-28"
                                placeholder="Limite"
                                value={raw}
                                onChange={(e) =>
                                  handleLimitChange(kpi.id, e.target.value)
                                }
                              />

                              <Button
                                onClick={() => saveLimit(kpi.id)}
                                disabled={disableSave}
                                className="min-w-[90px]"
                              >
                                {saving === kpi.id ? "Salvando..." : "Salvar"}
                              </Button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
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
