export const formatValue = (val: string | number | null) => {
  if (typeof val === "number") {
    return val.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
  }
  return val;
};

export const formatCategory = (value: string | null | undefined) => {
  if (!value) return "";

  return value
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
};

export function generateTimeSeries(kpiId: string, base: number) {
  const now = Date.now();
  return Array.from({ length: 10 }).map((_, i) => ({
    timestamp: new Date(now - (9 - i) * 3600_000).toLocaleTimeString("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
    }),
    value: base + Math.random() * 10 - 5,
  }));
}
