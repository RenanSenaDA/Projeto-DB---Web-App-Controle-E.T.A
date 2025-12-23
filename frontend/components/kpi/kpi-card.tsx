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

/**
 * Mapa de cores para estilização dinâmica dos cards.
 * Define borda, texto e fundo baseados em classes do Tailwind.
 */
const COLOR_MAP: Record<string, StyleTriplet> = {
  "bg-blue-600": { border: "border-l-blue-600", text: "text-blue-600", bg: "bg-blue-50" },
  "bg-emerald-600": { border: "border-l-emerald-600", text: "text-emerald-600", bg: "bg-emerald-50" },
  "bg-amber-500": { border: "border-l-amber-500", text: "text-amber-500", bg: "bg-amber-50" },
  "bg-red-500": { border: "border-l-red-500", text: "text-red-500", bg: "bg-red-50" },
  "bg-violet-600": { border: "border-l-violet-600", text: "text-violet-600", bg: "bg-violet-50" },
  "bg-indigo-600": { border: "border-l-indigo-600", text: "text-indigo-600", bg: "bg-indigo-50" },
  "bg-teal-600": { border: "border-l-teal-600", text: "text-teal-600", bg: "bg-teal-50" },
  "bg-cyan-600": { border: "border-l-cyan-600", text: "text-cyan-600", bg: "bg-cyan-50" },
  "bg-rose-500": { border: "border-l-rose-500", text: "text-rose-500", bg: "bg-rose-50" },
  "bg-orange-500": { border: "border-l-orange-500", text: "text-orange-500", bg: "bg-orange-50" },
  "bg-lime-600": { border: "border-l-lime-600", text: "text-lime-600", bg: "bg-lime-50" },
  "bg-fuchsia-600": { border: "border-l-fuchsia-600", text: "text-fuchsia-600", bg: "bg-fuchsia-50" },
}

/**
 * Deriva os estilos visuais com base na classe de cor fornecida.
 * Se a cor não for encontrada, retorna um estilo padrão cinza.
 * @param colorClass Classe de cor (ex: "bg-blue-600")
 */
function deriveStyles(colorClass?: string): StyleTriplet {
  if (!colorClass || !COLOR_MAP[colorClass]) {
    return { border: "border-l-muted-foreground/40", text: "text-muted-foreground", bg: "bg-muted" }
  }
  return COLOR_MAP[colorClass]
}

/**
 * Componente Card de KPI.
 * Exibe o valor atual, unidade, limite e status de uma métrica.
 * Visualiza alertas se o valor exceder o limite configurado.
 * 
 * @component
 */
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
        "group relative overflow-hidden bg-card transition-all duration-300 hover:shadow-md border border-border border-l-4",
        styles.border,
        className
      )}
    >
      <CardHeader className="flex items-start justify-between pb-2 space-y-0">
        <CardTitle className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
          {label}
        </CardTitle>

        {aboveLimit && (
          <CardAction className="flex flex-col items-end gap-1">
            <Badge className="text-xs text-destructive bg-destructive/10 border border-destructive">Acima do limite</Badge>
          </CardAction>
        )}
      </CardHeader>

      <CardContent className="space-y-4 relative z-10">
        <div className="flex items-end justify-between mt-1">
          {/* Valor Atual */}
          <div>
            <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide block mb-1">
              Atual
            </span>
            <div className="flex items-baseline gap-1">
              <span className={cn("text-2xl font-bold tracking-tight", styles.text)}>
                {formatValue(value)}
              </span>
              <span className="text-sm font-medium text-muted-foreground">
                {unit}
              </span>
            </div>
          </div>

          {/* Limite */}
          {limit !== undefined && limit !== null && (
            <div className="text-right">
              <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide block mb-1">
                Limite
              </span>
              <div className="flex items-baseline justify-end gap-1">
                <span className="text-lg font-semibold text-foreground tracking-tight">
                  {formatValue(limit)}
                </span>
                <span className="text-[10px] font-medium text-muted-foreground">
                  {unit}
                </span>
              </div>
            </div>
          )}
        </div>

        <div className="pt-3 border-t border-border flex items-center justify-start gap-2">
          <p className="text-xs text-muted-foreground tabular-nums">
            Última atualização {formatRelativeTime(updated_at)}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
