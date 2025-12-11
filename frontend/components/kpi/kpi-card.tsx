import {
  Card,
  CardAction,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/ui/card";
import { cn } from "@/lib/utils";
import type { KPIData } from "@/types/kpi";
import { formatValue, formatRelativeTime } from "@/lib/format";
import { Badge } from "@/ui/badge";

type StyleTriplet = { border: string; text: string; bg: string }

function deriveStyles(colorClass?: string): StyleTriplet {
  if (!colorClass || !colorClass.startsWith("bg-")) {
    return { border: "border-l-slate-400", text: "text-slate-500", bg: "bg-slate-100" }
  }
  const border = colorClass.replace("bg-", "border-l-")
  const text = colorClass.replace("bg-", "text-")
  const bg = colorClass.replace(/(600|500|400|300|200|100)/, "50")
  return { border, text, bg }
}

export default function KPICard({
  label,
  unit,
  updated_at,
  value,
  limit,
  className,
  colorClass,
}: Omit<KPIData, "category"> & { className?: string; colorClass?: string }) {
  const styles = deriveStyles(colorClass)
  const aboveLimit =
    value !== null &&
    value !== undefined &&
    limit !== null &&
    limit !== undefined &&
    Number(value) > Number(limit);

  return (
    <Card
      className={cn(
        "group relative overflow-hidden bg-white transition-all duration-300 hover:shadow-md border border-slate-200 border-l-4",
        styles.border,
        className
      )}
    >
      <CardHeader className="flex items-start justify-between pb-2 space-y-0">
        <CardTitle className="text-xs font-bold text-slate-600 uppercase tracking-wider">
          {label}
        </CardTitle>

        {aboveLimit && (
          <CardAction className="flex flex-col items-end gap-1">
            <Badge variant="destructive">Acima do limite</Badge>
          </CardAction>
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="flex items-end justify-between mt-1">
          {/* Valor Atual */}
          <div>
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide block mb-1">
              Atual
            </span>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold text-[#00283F] tracking-tight">
                {formatValue(value)}
              </span>
              <span className="text-xs font-medium text-[#00283F]">{unit}</span>
            </div>
          </div>

          {/* Limite */}
          {limit !== undefined && limit !== null && (
            <div className="text-right">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide block mb-1">
                Limite
              </span>
              <div className="flex items-baseline justify-end gap-1">
                <span className="text-lg font-semibold text-slate-600 tracking-tight">
                  {formatValue(limit)}
                </span>
                <span className="text-[10px] font-medium text-slate-400">
                  {unit}
                </span>
              </div>
            </div>
          )}
        </div>

        <div className="pt-3 border-t border-slate-100 flex items-center justify-start gap-2">
          <p className="text-xs text-slate-400 tabular-nums">
            Última atualização {formatRelativeTime(updated_at)}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
