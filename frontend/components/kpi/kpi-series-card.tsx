"use client";

import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  type TooltipProps,
} from "recharts";

import { ChartContainer, ChartTooltip } from "@/ui/chart";
import { Card, CardContent, CardHeader, CardTitle } from "@/ui/card";
import { formatRelativeTime } from "@/lib/format";

interface KPIData {
  id: string;
  label: string;
  value?: number | null;
  unit: string;
  updated_at: string;
}

/**
 * Ponto de dado para o gráfico de série temporal.
 */
export interface TimeSeriesPoint {
  /** Timestamp ISO string */
  ts: string;
  /** Rótulo formatado para o eixo X */
  label: string;
  /** Valor numérico da medição */
  value: number;
}

/**
 * Propriedades do Card de Série Temporal.
 */
interface KpiSeriesCardProps {
  /** Metadados da KPI (nome, unidade, etc.) */
  kpi: KPIData;
  /** Array de pontos de dados históricos */
  timeSeries: TimeSeriesPoint[];
}

/**
 * Tooltip customizado para o gráfico Recharts.
 * Exibe valor, data e hora detalhados ao passar o mouse.
 */
function CustomTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload || !payload.length) return null;
  const item = payload[0]?.payload as {
    ts: string;
    label: string;
    value: number;
  };
  const d = new Date(item.ts);
  const data = d.toLocaleDateString("pt-BR");
  const hora = d.toLocaleTimeString("pt-BR");

  return (
    <div className="min-w-40 rounded-lg border bg-white px-3 py-2 shadow-lg">
      <div className="flex flex-col gap-1 text-sm">
        <div className="flex justify-between">
          <span className="text-neutral-500">Valor</span>
          <span className="font-medium text-neutral-800">
            {item.value.toFixed(2)}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-neutral-500">Data</span>
          <span className="font-medium text-neutral-800">{data}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-neutral-500">Horário</span>
          <span className="font-medium text-neutral-800">{hora}</span>
        </div>
      </div>
    </div>
  );
}

/**
 * Componente Card de Gráfico de Série Temporal.
 * Renderiza um gráfico de área ou linha dependendo da densidade de dados.
 * Inclui gradientes, tooltips e informação de última atualização.
 * 
 * @component
 */
export default function KpiSeriesCard({ kpi, timeSeries }: KpiSeriesCardProps) {
  const pointCount = timeSeries.length;
  const isDense = pointCount >= 60;
  const isMedium = pointCount >= 20 && pointCount < 60;
  const gradId = `grad-${kpi.id}`;
  return (
    <Card className="w-full border rounded-xl shadow-sm hover:shadow-md transition-all">
      <CardHeader>
        <CardTitle>
          {kpi.label ? kpi.label[0].toUpperCase() + kpi.label.slice(1) : ""}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ChartContainer
          config={{ value: { label: kpi.label, color: "var(--color-primary)" } }}
          className="h-[300px] w-full"
        >
          {isDense ? (
            <AreaChart width={335} height={300} data={timeSeries}>
              <defs>
                <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--color-primary)" stopOpacity={0.25} />
                  <stop offset="100%" stopColor="var(--color-primary)" stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="2 2" />
              <XAxis dataKey="label" tick={{ fontSize: 12 }} stroke="var(--color-border)" />
              <YAxis tick={{ fontSize: 12 }} stroke="var(--color-border)" domain={["auto", "auto"]} />
              <ChartTooltip cursor={{ stroke: "var(--color-border)", strokeDasharray: "4 4" }} content={<CustomTooltip />} />
              <Area
                type="natural"
                dataKey="value"
                stroke="var(--color-primary)"
                strokeWidth={1.8}
                fill={`url(#${gradId})`}
                dot={false}
                activeDot={{ r: 3 }}
              />
            </AreaChart>
          ) : (
            <LineChart width={335} height={300} data={timeSeries}>
              <CartesianGrid strokeDasharray="2 2" />
              <XAxis dataKey="label" tick={{ fontSize: 12 }} stroke="var(--color-border)" />
              <YAxis tick={{ fontSize: 12 }} stroke="var(--color-border)" domain={["auto", "auto"]} />
              <ChartTooltip cursor={{ stroke: "var(--color-border)", strokeDasharray: "4 4" }} content={<CustomTooltip />} />
              <Line
                type="natural"
                dataKey="value"
                stroke="var(--color-primary)"
                strokeWidth={1.8}
                dot={
                  isMedium
                    ? false
                    : ({ cx, cy }) => (
                        <circle cx={cx} cy={cy} r={3} fill="var(--color-primary)" />
                      )
                }
                activeDot={{ r: 4 }}
              />
            </LineChart>
          )}
        </ChartContainer>
        <div className="pt-3 border-t border-slate-100 flex items-center justify-start gap-2">
          <p className="text-xs text-slate-400 tabular-nums">
            Última atualização {formatRelativeTime(kpi.updated_at)}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
