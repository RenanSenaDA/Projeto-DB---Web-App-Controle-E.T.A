import { createDashboardService } from "@/services/dashboard";
import { defaultHttpClient } from "@/services/http";
import DashboardClient from "./dashboard-client";

// Server Component: Realiza o fetch inicial no servidor
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
