import { Card, CardContent, CardHeader, CardTitle } from "@/ui/card";
import { Badge } from "@/ui/badge";
import { cn } from "@/lib/utils";
import { formatValue, formatRelativeTime } from "@/lib/format";

type StyleTriplet = { border: string; text: string; bg: string };

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
};

function deriveStyles(colorClass?: string): StyleTriplet {
  if (!colorClass || !COLOR_MAP[colorClass]) {
    return { border: "border-l-muted-foreground/40", text: "text-muted-foreground", bg: "bg-muted" };
  }
  return COLOR_MAP[colorClass];
}

type KPIItem = {
  id?: string;
  label: string;
  unit?: string | null;
  updated_at?: string | null;
  value?: number | string | null;
  limit?: number | string | null;
};

function isAboveLimit(value: any, limit: any) {
  if (value === null || value === undefined) return false;
  if (limit === null || limit === undefined) return false;
  const v = Number(value);
  const l = Number(limit);
  if (!Number.isFinite(v) || !Number.isFinite(l)) return false;
  return v > l;
}

export default function KPICardDual({
  title = "Indicador",
  leftLabel,
  rightLabel,
  left,
  right,
  className,
  colorClass,
}: {
  title?: string;
  leftLabel: string;
  rightLabel: string;
  left: KPIItem | null;
  right: KPIItem | null;
  className?: string;
  colorClass?: string;
}) {
  const styles = deriveStyles(colorClass);

  const leftAbove = isAboveLimit(left?.value, left?.limit);
  const rightAbove = isAboveLimit(right?.value, right?.limit);
  const anyAbove = leftAbove || rightAbove;

  // pega a atualização mais recente entre os dois
  const updatedAt =
    [left?.updated_at, right?.updated_at].filter(Boolean).sort().at(-1) ?? null;

  const showLeftLimit = left?.limit !== null && left?.limit !== undefined;
  const showRightLimit = right?.limit !== null && right?.limit !== undefined;

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
          {title}
        </CardTitle>

        {anyAbove && (
          <div className="flex flex-col items-end gap-1">
            <Badge className="text-xs text-destructive bg-destructive/10 border border-destructive">
              Acima do limite
            </Badge>
          </div>
        )}
      </CardHeader>

      <CardContent className="space-y-4 relative z-10">
        <div className="grid grid-cols-2 gap-6">
          {/* LEFT */}
          <div className="space-y-2">
            <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide block">
              {leftLabel}
            </span>

            {/* Atual */}
            <div className="flex items-baseline gap-1">
              <span className={cn("text-2xl font-bold tracking-tight", styles.text)}>
                {formatValue(left?.value ?? null)}
              </span>
              <span className="text-sm font-medium text-muted-foreground">
                {left?.unit ?? "un"}
              </span>
            </div>

            {/* Limite */}
            {showLeftLimit && (
              <div className="pt-1">
                <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide block mb-1">
                  Limite
                </span>
                <div className="flex items-baseline gap-1">
                  <span className="text-sm font-semibold text-foreground tracking-tight">
                    {formatValue(left?.limit ?? null)}
                  </span>
                  <span className="text-[10px] font-medium text-muted-foreground">
                    {left?.unit ?? "un"}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* RIGHT */}
          <div className="space-y-2">
            <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide block">
              {rightLabel}
            </span>

            {/* Atual */}
            <div className="flex items-baseline gap-1">
              <span className={cn("text-2xl font-bold tracking-tight", styles.text)}>
                {formatValue(right?.value ?? null)}
              </span>
              <span className="text-sm font-medium text-muted-foreground">
                {right?.unit ?? "un"}
              </span>
            </div>

            {/* Limite */}
            {showRightLimit && (
              <div className="pt-1">
                <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide block mb-1">
                  Limite
                </span>
                <div className="flex items-baseline gap-1">
                  <span className="text-sm font-semibold text-foreground tracking-tight">
                    {formatValue(right?.limit ?? null)}
                  </span>
                  <span className="text-[10px] font-medium text-muted-foreground">
                    {right?.unit ?? "un"}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="pt-3 border-t border-border flex items-center justify-start gap-2">
          <p className="text-xs text-muted-foreground tabular-nums">
            Última atualização {updatedAt ? formatRelativeTime(updatedAt) : "—"}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

