/**
 * Utilitários para formatação de dados e datas.
 *
 * Este arquivo contém funções auxiliares para formatar valores numéricos,
 * datas relativas e outras representações visuais de dados.
 */

import { formatDistanceToNow } from "date-fns";
import { ptBR } from "date-fns/locale";

/**
 * Formata um valor numérico para exibição.
 *
 * @param value - O valor a ser formatado (number ou string numérica).
 * @param decimals - O número de casas decimais (padrão: 2).
 * @returns Uma string formatada ou "N/A" se o valor for inválido.
 *
 * @example
 * formatValue(123.456) // "123.46"
 * formatValue(null) // "N/A"
 */
export function formatValue(
  value: number | string | undefined | null,
  decimals = 2
): string {
  if (value === undefined || value === null || value === "") return "N/A";
  const n = Number(value);
  if (isNaN(n)) return "N/A";
  return n.toLocaleString("pt-BR", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

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

/**
 * Retorna uma string representando o tempo decorrido desde a data fornecida até agora.
 *
 * @param date - A data passada (string ou Date).
 * @returns String como "há 5 minutos", "há 2 dias", etc.
 *
 * @example
 * formatRelativeTime(new Date(Date.now() - 60000)) // "há cerca de 1 minuto"
 */
export function formatRelativeTime(date: string | Date): string {
  if (!date) return "";
  return formatDistanceToNow(new Date(date), {
    addSuffix: true,
    locale: ptBR,
  });
}
