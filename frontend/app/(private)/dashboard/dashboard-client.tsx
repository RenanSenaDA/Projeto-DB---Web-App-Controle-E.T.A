"use client";

import { Tabs, TabsContent } from "@/ui/tabs";

import KPICard from "@/components/kpi/kpi-card";
import KPICardDual from "@/components/kpi/kpi-card-dual";
import Error from "@/components/feedback/error";
import PageHeader from "@/components/header-page";
import Loading from "@/components/feedback/loading";
import KPISection from "@/components/kpi/kpi-section";
import EmptyState from "@/components/feedback/empty-state";
import TabsListStation from "@/components/tabs-list-station";

import type { KPIData, ApiResponse } from "@/types/kpi";
import { useDashboardViewModel } from "@/hooks/view/use-dashboard-view-model";

interface DashboardClientProps {
  initialData?: ApiResponse | null;
}

/** Remove acentos + normaliza espaços/símbolos para comparação robusta */
function normalizeText(input: any) {
  return String(input ?? "")
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "") // remove diacríticos (acentos)
    .replace(/\s+/g, " ") // colapsa espaços
    .replace(/[\/\-_:]+/g, " ") // troca separadores por espaço
    .replace(/[^\p{L}\p{N}\s]/gu, "") // remove pontuação
    .trim();
}

/** Pega o "título humano" (último segmento após /) */
function tailSegment(labelOrTag: any) {
  const raw = String(labelOrTag ?? "").trim();
  if (!raw) return "";
  const parts = raw.split("/").filter(Boolean);
  return parts.length ? parts[parts.length - 1] : raw;
}

/** Compara KPI com alvo usando:
 *  - match pelo label completo normalizado
 *  - ou pelo último segmento (título) normalizado
 */
function matches(kpi: KPIData, targetTagOrLabel: string) {
  const kLabel = String(kpi.label ?? "").trim();

  const a1 = normalizeText(kLabel);
  const b1 = normalizeText(targetTagOrLabel);
  if (a1 === b1) return true;

  const a2 = normalizeText(tailSegment(kLabel));
  const b2 = normalizeText(tailSegment(targetTagOrLabel));
  return a2 === b2;
}

/**
 * ✅ Fallback adicional (muito robusto):
 * tenta casar por palavras-chave no label OU no id.
 * Ex: "retrolavagem m3/h", "retrolavagem m3/dia"
 */
function matchesByKeywords(kpi: KPIData, keywords: string[]) {
  const hay = normalizeText(`${kpi.id ?? ""} ${kpi.label ?? ""}`);
  return keywords.every((kw) => hay.includes(normalizeText(kw)));
}

export default function DashboardClient({ initialData }: DashboardClientProps) {
  const {
    loading,
    error,
    fetchData,
    stationKeys,
    stationsList,
    categoryMap,
    getKPIs,
    hasData,
  } = useDashboardViewModel(initialData);

  if (loading) return <Loading />;
  if (error) return <Error error={error} fetchData={fetchData} />;

  // Renderiza a lista de cards de KPI para uma seção específica (com suporte a cards compostos)
  const renderCardList = (kpis: KPIData[], colorClass?: string) => {
    let remaining = [...kpis];
    const dualCards: React.ReactNode[] = [];

    const pickAny = (targets: string[], fallbackKeywords?: string[]) => {
      const t = targets.find((x) => remaining.some((k) => matches(k, x)));
      if (t) return remaining.find((k) => matches(k, t)) ?? null;

      if (fallbackKeywords?.length) {
        return remaining.find((k) => matchesByKeywords(k, fallbackKeywords)) ?? null;
      }

      return null;
    };

    // ✅ Versão robusta: aceita aliases + fallback por keywords
    const tryGroup = (
      title: string,
      leftLabel: string,
      rightLabel: string,
      leftTargets: string[],
      rightTargets: string[],
      leftFallbackKeywords?: string[],
      rightFallbackKeywords?: string[]
    ) => {
      const left = pickAny(leftTargets, leftFallbackKeywords);
      const right = pickAny(rightTargets, rightFallbackKeywords);

      if (!left || !right) return;

      dualCards.push(
        <KPICardDual
          key={`${title}-${leftLabel}-${rightLabel}`}
          title={title}
          leftLabel={leftLabel}
          rightLabel={rightLabel}
          left={left}
          right={right}
          colorClass={colorClass}
          className="h-full"
        />
      );

      // remove exatamente os KPIs usados
      remaining = remaining.filter((k) => k.id !== left.id && k.id !== right.id);
    };

    // ===== ETA =====

    // 1 + 2
    tryGroup(
      "Tempo de Inatividade Não Planejada",
      "Por Hora",
      "Por Mês",
      ["eta/integridade alarmes/Tempo de Inatividade não Planejada por Hora"],
      ["eta/integridade alarmes/Tempo de Inatividade não Planejada por Mês"],
      ["inatividade", "hora"],
      ["inatividade", "mes"]
    );

    // Retrolavagens (Semanal + Mensal)
    tryGroup(
      "Frequência de Retrolavagens",
      "Semanal",
      "Mensal",
      ["eta/limpeza/Frequência de Retrolavagens Semanal"],
      ["eta/limpeza/Frequência de Retrolavagens Mensal"],
      ["frequencia", "retrolav", "semanal"],
      ["frequencia", "retrolav", "mensal"]
    );

    // Descarte (Semanal + Mensal)
    tryGroup(
      "Frequência do Descarte de Lodo",
      "Semanal",
      "Mensal",
      ["eta/limpeza/Frequência do Descarte de Lodo Semanal"],
      ["eta/limpeza/Frequência do Descarte de Lodo Mensal"],
      ["frequencia", "descarte", "lodo", "semanal"],
      ["frequencia", "descarte", "lodo", "mensal"]
    );

    // Alimentação (M3/h + M3/dia)
    tryGroup(
      "Fluxo de Alimentação",
      "M3/h",
      "M3/dia",
      ["eta/operacional/Fluxo Alimentação M3/h", "eta/operacional/Fluxo de Alimentação M3/h"],
      ["eta/operacional/Fluxo de alimentação M3/dia", "eta/operacional/Fluxo de Alimentação M3/dia"],
      ["fluxo", "aliment", "m3", "h"],
      ["fluxo", "aliment", "m3", "dia"]
    );

    // ✅ Retrolavagem (M3/h + M3/dia) — agora NÃO depende de "de"
    tryGroup(
      "Fluxo de Retrolavagem",
      "M3/h",
      "M3/dia",
      [
        "eta/operacional/Fluxo Retrolavagem M3/h",
        "eta/operacional/Fluxo de Retrolavagem M3/h",
      ],
      [
        "eta/operacional/Fluxo Retrolavagem M3/dia",
        "eta/operacional/Fluxo de Retrolavagem M3/dia",
      ],
      ["fluxo", "retrolav", "m3", "h"],
      ["fluxo", "retrolav", "m3", "dia"]
    );

    // ===== CARVÃO (fc) =====

    // Alimentação (M3/h + M3/dia)
    tryGroup(
      "Fluxo de Alimentação (Carvão)",
      "M3/h",
      "M3/dia",
      ["fc/operacional/Fluxo de Alimentação M3/h", "fc/operacional/Fluxo Alimentação M3/h"],
      ["fc/operacional/Fluxo de Alimentação M3/dia", "fc/operacional/Fluxo Alimentação M3/dia"],
      ["fc", "fluxo", "aliment", "m3", "h"],
      ["fc", "fluxo", "aliment", "m3", "dia"]
    );

    // ✅ Retrolavagem (M3/h + M3/dia) — robusto por keywords
    tryGroup(
      "Fluxo de Retrolavagem (Carvão)",
      "M3/h",
      "M3/dia",
      [
        "fc/operacional/Fluxo de Retrolavagem M3/h",
        "fc/operacional/Fluxo Retrolavagem M3/h",
      ],
      [
        "fc/operacional/Fluxo de Retrolavagem M3/dia",
        "fc/operacional/Fluxo Retrolavagem M3/dia",
      ],
      ["fc", "fluxo", "retrolav", "m3", "h"],
      ["fc", "fluxo", "retrolav", "m3", "dia"]
    );

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
        {dualCards}
        {remaining.map((kpi) => (
          <KPICard
            key={kpi.id}
            {...kpi}
            colorClass={colorClass}
            className="h-full"
          />
        ))}
      </div>
    );
  };

  return (
    <div className="container mx-auto min-h-screen p-6 font-sans">
      <div className="flex justify-between items-center">
        <PageHeader
          title="Dashboard de Monitoramento"
          subtitle="Visão geral das estações em tempo real"
        />
      </div>

      {hasData ? (
        <Tabs defaultValue={stationKeys[0]} className="w-full">
          <TabsListStation stations={stationsList} />

          {stationKeys.map((stationKey) => (
            <TabsContent
              key={stationKey}
              value={stationKey}
              className="space-y-8 animate-in fade-in-50 duration-300"
            >
              {Object.entries(categoryMap).map(([category, config]) => {
                const sectionKPIs = getKPIs(stationKey, category);
                if (!sectionKPIs.length) return null;

                return (
                  <KPISection
                    key={category}
                    color={config.color}
                    title_section={config.title}
                  >
                    {renderCardList(sectionKPIs, config.color)}
                  </KPISection>
                );
              })}
            </TabsContent>
          ))}
        </Tabs>
      ) : (
        <EmptyState
          title="Nenhuma estação disponível"
          description="Não há dados de monitoramento para exibir no momento."
        />
      )}
    </div>
  );
}
