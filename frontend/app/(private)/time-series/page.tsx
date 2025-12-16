import { createDashboardService } from "@/services/dashboard";
import { defaultHttpClient } from "@/services/http";
import TimeSeriesClient from "./time-series-client";

export default async function TimeSeriesPage() {
  const svc = createDashboardService(defaultHttpClient);
  let initialData = null;

  try {
    initialData = await svc.getDashboard();
  } catch (e) {
    console.error("Falha ao carregar dados iniciais no servidor:", e);
  }

  return <TimeSeriesClient initialData={initialData} />;
}
