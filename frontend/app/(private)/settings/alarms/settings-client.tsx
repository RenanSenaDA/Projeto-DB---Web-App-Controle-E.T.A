"use client";

import { Tabs, TabsContent } from "@/ui/tabs";
import { Button } from "@/ui/button";
import { Input } from "@/ui/input";

import Loading from "@/components/feedback/loading";
import SectionLabel from "@/components/label-section";
import TabsListStation from "@/components/tabs-list-station";

import type { ApiResponse } from "@/types/kpi";
import { formatValue } from "@/lib/format";
import { cn } from "@/lib/utils";
import { Save } from "lucide-react";
import { useLimitsViewModel } from "@/hooks/view/use-limits-view-model";

interface LimitsClientProps {
  initialData?: ApiResponse | null;
}

/**
 * Componente Cliente de Configurações.
 * Permite ajustar limites de alarme para cada KPI e ativar/desativar alarmes globais.
 * Usa useLimitsViewModel para lógica de persistência e feedback.
 */
export default function LimitsClient({ initialData }: LimitsClientProps) {        
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
  } = useLimitsViewModel  (initialData);

  if (loading) return <Loading />;
  if (error) return <p className="text-red-500 p-6">Erro ao carregar dados.</p>;
  if (!data) return null;

  return (
    <div className="space-y-8">
      {/* Header da Seção */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center pb-6 border-b gap-4">
        <div>
          <h2 className="text-xl font-semibold text-foreground">
            Limites de Alarme
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Defina os limites operacionais para alertas automáticos de cada
            sensor.
          </p>
        </div>

        <div className="flex items-center gap-4 bg-muted/50 p-3 rounded-lg border">
          <div className="flex flex-col items-end mr-2">
            <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-0.5">
              Monitoramento
            </span>
            <span
              className={cn(
                "text-sm font-bold flex items-center gap-2",
                alarmsEnabled ? "text-emerald-600" : "text-rose-600"
              )}
            >
              <span
                className={cn(
                  "w-2 h-2 rounded-full",
                  alarmsEnabled ? "bg-emerald-500" : "bg-rose-500 animate-pulse"
                )}
              />
              {alarmsLoading ? "..." : alarmsEnabled ? "ATIVADO" : "DESATIVADO"}
            </span>
          </div>
          <Button
            onClick={toggleAlarms}
            disabled={alarmsLoading || toggling || alarmsEnabled === null}
            size="sm"
            className={cn(
              "text-white min-w-[100px] shadow-sm transition-all",
              alarmsEnabled
                ? "bg-rose-600 hover:bg-rose-700 hover:shadow-md"
                : "bg-emerald-600 hover:bg-emerald-700 hover:shadow-md"
            )}
          >
            {toggling ? "..." : alarmsEnabled ? "Desativar" : "Ativar"}
          </Button>
        </div>
      </div>

      <Tabs defaultValue={stationKeys[0] ?? ""} className="w-full">
        <TabsListStation stations={stationsList} />

        {stationKeys.map((key) => (
          <TabsContent
            key={key}
            value={key}
            className="mt-6 animate-in fade-in-50 duration-300"
          >
            {Object.entries(categoryMap).map(([category, config]) => {
              const sectionItems = getKPIsForStationAndCategory(key, category);
              if (!sectionItems.length) return null;

              return (
                <div key={category} className="mb-8">
                  <SectionLabel title={config.title} color={config.color} />
                  <div className="grid gap-3 mt-4">
                    {sectionItems.map((kpi) => (
                      <div
                        key={kpi.id}
                        className="group p-4 bg-card hover:bg-muted/50 transition-colors rounded-xl border border-border flex flex-col sm:flex-row gap-4 justify-between items-center"
                      >
                        <div className="flex-1 w-full text-left">
                          <p className="font-semibold text-foreground">
                            {kpi.label}
                          </p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs font-medium text-muted-foreground uppercase">
                              Atual
                            </span>
                            <span className="text-sm font-medium text-foreground bg-muted px-2 py-0.5 rounded">
                              {formatValue(kpi.value)} {kpi.unit || ""}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-3 w-full sm:w-auto">
                          <div className="relative w-full sm:w-32">
                            <Input
                              type="number"
                              className="pr-8 text-right font-medium"
                              placeholder="Limite"
                              value={limits[kpi.id] ?? ""}
                              onChange={(e) =>
                                handleLimitChange(kpi.id, e.target.value)
                              }
                            />
                            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground pointer-events-none">
                              Max
                            </span>
                          </div>

                          <Button
                            onClick={() => saveLimit(kpi.id)}
                            disabled={
                              limits[kpi.id] === null ||
                              saving === kpi.id ||
                              limits[kpi.id] === (kpi.limit ?? null)
                            }
                            size="icon"
                            variant={
                              limits[kpi.id] !== (kpi.limit ?? null)
                                ? "default"
                                : "ghost"
                            }
                            className={cn(
                              "shrink-0 transition-all",
                              limits[kpi.id] !== (kpi.limit ?? null)
                                ? "bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm w-10 h-10"
                                : "text-muted-foreground hover:text-primary w-10 h-10"
                            )}
                            title="Salvar alteração"
                          >
                            {saving === kpi.id ? (
                              <span className="animate-spin rounded-full h-4 w-4 border-2 border-current border-t-transparent" />
                            ) : (
                              <Save className="w-4 h-4" />
                            )}
                          </Button>
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
