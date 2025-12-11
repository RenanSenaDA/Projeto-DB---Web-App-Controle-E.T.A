import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import type { ApiResponse } from "@/types/kpi"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function getApiBase() {
  return process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
}

export function idToTag(id: string) {
  return id.replace(/_/g, "/")
}

const CATEGORY_COLORS = [
  "bg-blue-600",
  "bg-emerald-600",
  "bg-amber-500",
  "bg-red-500",
  "bg-violet-600",
  "bg-indigo-600",
  "bg-teal-600",
  "bg-cyan-600",
  "bg-rose-500",
  "bg-orange-500",
  "bg-lime-600",
  "bg-fuchsia-600",
]

export function toCategoryTitle(slug: string) {
  const s = (slug || "").replace(/_/g, " ").trim()
  return s
    .split(" ")
    .filter(Boolean)
    .map((w) => w[0]?.toUpperCase() + w.slice(1))
    .join(" ")
}

export function buildCategoryMap(data: ApiResponse | null | undefined) {
  const found = new Set<string>()
  if (data?.data) {
    for (const station of Object.values(data.data)) {
      for (const k of station.kpis || []) {
        if (k.category) found.add(k.category)
      }
    }
  }
  const names = Array.from(found).sort()
  const map: Record<string, { color: string; title: string }> = {}
  names.forEach((name, i) => {
    map[name] = {
      color: CATEGORY_COLORS[i % CATEGORY_COLORS.length],
      title: toCategoryTitle(name),
    }
  })
  if (!names.length) {
    map.default = { color: "bg-slate-400", title: "Seção" }
  }
  return map
}
