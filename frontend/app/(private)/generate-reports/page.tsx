import { createDashboardService } from "@/services/dashboard";
import { defaultHttpClient } from "@/services/http";
import ReportsClient from "./reports-client";

/**
 * Página de Relatórios (Server Component).
 * Busca dados iniciais para popular o seletor de KPIs.
 */
export default async function ReportsPage() {
  const svc = createDashboardService(defaultHttpClient);
  let initialData = null;

  try {
    initialData = await svc.getDashboard();
  } catch (e) {
    console.error("Falha ao carregar dados iniciais no servidor:", e);
  }

  return <ReportsClient initialData={initialData} />;
}
