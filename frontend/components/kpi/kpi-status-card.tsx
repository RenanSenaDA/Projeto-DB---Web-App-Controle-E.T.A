import type { KPIStatusOperation } from "@/types/kpi";
import { Card, CardHeader, CardTitle } from "@/ui/card";
import { Badge } from "@/ui/badge";

export interface KPIStatusCardProps {
  value: KPIStatusOperation | string | null;
}

export default function KPIStatusCard({ value }: KPIStatusCardProps) {
  const statusText = value ?? "Indeterminado";

  const colors = {
    operação: {
      bg: "bg-green-50",
      border: "border-l-green-600",
      badge: "text-green-700 border-green-700 bg-green-100",
    },
    parado: {
      bg: "bg-red-50",
      border: "border-l-red-600",
      badge: "text-red-700 border-red-700 bg-red-100",
    },
    retrolavagem: {
      bg: "bg-blue-50",
      border: "border-l-blue-600",
      badge: "text-blue-700 border-blue-700 bg-blue-100",
    },
    sanitização: {
      bg: "bg-amber-50",
      border: "border-l-amber-600",
      badge: "text-amber-700 border-amber-700 bg-amber-100",
    },
    default: {
      bg: "bg-slate-50",
      border: "border-l-slate-400",
      badge: "text-slate-600 border-slate-600 bg-slate-100",
    },
  };

  const { bg, border, badge } =
    colors[value as KPIStatusOperation] ?? colors.default;

  return (
    <Card
      className={`border border-slate-200 shadow-sm mb-4 border-l-4 ${bg} ${border}`}
    >
      <CardHeader className="flex items-center justify-between">
        <CardTitle className="text-xs font-bold text-slate-600 uppercase tracking-wider">
          STATUS DO FILTRO
        </CardTitle>

        <Badge
          variant="outline"
          className={`${badge} px-2 py-0.5 text-xs font-semibold`}
        >
          Em {statusText}
        </Badge>
      </CardHeader>
    </Card>
  );
}
