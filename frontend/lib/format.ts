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

export const formatRelativeTime = (ts: string | Date | null | undefined) => {
  if (!ts) return "--";
  const d = ts instanceof Date ? ts : new Date(ts as string);
  if (isNaN(d.getTime())) return "--";
  const diffMs = Date.now() - d.getTime();
  if (diffMs < 0) return "agora";
  const sec = Math.floor(diffMs / 1000);
  if (sec < 60) return `há ${sec}s`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `há ${min} min`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `há ${hr} h`;
  const day = Math.floor(hr / 24);
  return `há ${day} d`;
};
