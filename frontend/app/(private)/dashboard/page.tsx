import { createDashboardService } from "@/services/dashboard";
import { defaultHttpClient } from "@/services/http";
import DashboardClient from "./dashboard-client";
export const dynamic = "force-dynamic";
/**
 * Página do Dashboard (Server Component).
 * Realiza o fetch inicial dos dados no servidor para melhor performance (SSR).
 * Se o fetch falhar, a página carrega mesmo assim e o cliente tenta buscar novamente.
 */
export default async function DashboardPage() {
  const svc = createDashboardService(defaultHttpClient);
  let initialData = null;

  try {
    initialData = await svc.getDashboard();
  } catch (e) {
    console.error("Falha ao carregar dados iniciais no servidor:", e);
    // Não falhamos a página inteira, deixamos o cliente tentar buscar novamente
    // ou mostrar o erro através do hook useApi
  }

  return <DashboardClient initialData={initialData} />;
}
