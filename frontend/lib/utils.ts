import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function getApiBase() {
  return process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
}

export function idToTag(id: string) {
  return id.replace(/_/g, "/")
}
