import AlarmsClient from "./alarms-client";

export const dynamic = "force-dynamic";

/**
 * Página de Alarmes: histórico de eventos (com reconhecimento) e faixas (min/max).
 */
export default function AlarmsPage() {
  return <AlarmsClient />;
}
