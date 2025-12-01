// components/kpi/kpi-series-card.tsx
"use client";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  type TooltipProps,
} from "recharts";

import { ChartContainer, ChartTooltip } from "@/ui/chart";
import { Card, CardContent, CardHeader, CardTitle } from "@/ui/card";

interface KPIData {
  id: string;
  label: string;
  value?: number | null;
  unit: string;
}

export interface TimeSeriesPoint {
  timestamp: string;
  value: number;
}

interface KpiSeriesCardProps {
  kpi: KPIData;
  timeSeries: TimeSeriesPoint[];
}

export default function KpiSeriesCard({ kpi, timeSeries }: KpiSeriesCardProps) {
  const CustomTooltip = ({ active, payload }: TooltipProps<any, any>) => {
    if (!active || !payload || !payload.length) return null;

    const item = payload[0].payload;
    const now = new Date();
    const d = new Date(now);
    const [h, m] = item.timestamp.split(":");
    d.setHours(Number(h), Number(m));
    const dataCompleta = d.toLocaleDateString("pt-BR");

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
            <span className="font-medium text-neutral-800">{dataCompleta}</span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <Card className="w-full border rounded-xl shadow-sm hover:shadow-md transition-all">
      <CardHeader>
        <CardTitle>{`${kpi.label} (${kpi.unit})`}</CardTitle>
      </CardHeader>
      <CardContent>
        <ChartContainer
          config={{ value: { label: kpi.label, color: "#00B4F0" } }}
          className="h-[300px] w-full"
        >
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={timeSeries}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="timestamp"
                tick={{ fontSize: 12 }}
                stroke="#888"
              />
              <YAxis
                tick={{ fontSize: 12 }}
                stroke="#888"
                domain={["auto", "auto"]}
              />
              <ChartTooltip
                cursor={{ stroke: "#999", strokeDasharray: "5 5" }}
                content={<CustomTooltip active={false} payload={[]} />}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#00B4F0"
                strokeWidth={2}
                dot={({ cx, cy, payload }) => (
                  <circle
                    key={`${kpi.id}-${payload.timestamp}`}
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
          </ResponsiveContainer>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
