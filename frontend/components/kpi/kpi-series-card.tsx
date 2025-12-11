"use client";

import {
  LineChart,
  Line,
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

export interface TimeSeriesPoint {
  ts: string;
  label: string;
  value: number;
}

// Props: kpi (metadados), timeSeries (pontos para gráfico)
// Erros: valores inválidos são tratados pelo gráfico (domínio auto)
interface KpiSeriesCardProps {
  kpi: KPIData;
  timeSeries: TimeSeriesPoint[];
}

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

// Componente: exibe série temporal em linha para um KPI
// Intenção: facilitar análise visual com tooltip e última atualização
export default function KpiSeriesCard({ kpi, timeSeries }: KpiSeriesCardProps) {
  return (
    <Card className="w-full border rounded-xl shadow-sm hover:shadow-md transition-all">
      <CardHeader>
        <CardTitle>
          {kpi.label ? kpi.label[0].toUpperCase() + kpi.label.slice(1) : ""}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ChartContainer
          config={{ value: { label: kpi.label, color: "#00B4F0" } }}
          className="h-[300px] w-full"
        >
          <LineChart width={335} height={300} data={timeSeries}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="label" tick={{ fontSize: 12 }} stroke="#888" />
            <YAxis
              tick={{ fontSize: 12 }}
              stroke="#888"
              domain={["auto", "auto"]}
            />
            <ChartTooltip
              cursor={{ stroke: "#999", strokeDasharray: "5 5" }}
              content={<CustomTooltip />}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#00B4F0"
              strokeWidth={2}
              dot={({ cx, cy, payload }) => (
                <circle
                  key={`${kpi.id}-${payload.ts}`}
                  cx={cx}
                  cy={cy}
                  r={5}
                  stroke="white"
                  strokeWidth={2}
                  fill="#00B4F0"
                  className="transition-all hover:scale-125"
                />
              )}
            />
          </LineChart>
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
