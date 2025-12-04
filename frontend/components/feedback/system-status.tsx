"use client";

import useApi from "@/hooks/use-api";
import { cn } from "@/lib/utils";

export default function SystemStatus() {
  const { data, loading } = useApi();

  const isSystemOnline = data?.meta.status === "online";

  return (
    <div
      className={cn(
        "flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-full border shadow-sm transition-colors duration-300",
        loading
          ? "bg-amber-50 text-amber-600 border-amber-200"
          : isSystemOnline
          ? "bg-emerald-50 text-emerald-500 border-emerald-200"
          : "bg-rose-50 text-rose-700 border-rose-200"
      )}
    >
      <div
        className={cn(
          "h-2 w-2 rounded-full animate-pulse",
          loading ? "bg-amber-500" : isSystemOnline ? "bg-emerald-500" : "bg-rose-500"
        )}
      />
      <span>{loading ? "Verificando conexão..." : isSystemOnline ? "Sistema Online" : "Sistema Offline"}</span>
    </div>
  );
}
