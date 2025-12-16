import { createDashboardService } from "@/services/dashboard";
import { defaultHttpClient } from "@/services/http";
import SettingsClient from "./settings-client";

export default async function SettingsPage() {
  const svc = createDashboardService(defaultHttpClient);
  let initialData = null;

  try {
    initialData = await svc.getDashboard();
  } catch (e) {
    console.error("Falha ao carregar dados iniciais no servidor:", e);
  }

  return <SettingsClient initialData={initialData} />;
}
