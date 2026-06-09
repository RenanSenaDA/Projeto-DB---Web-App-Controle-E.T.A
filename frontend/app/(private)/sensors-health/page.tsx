import SensorsHealthClient from "./sensors-health-client";

export const dynamic = "force-dynamic";

/** Página de saúde dos sensores (observabilidade da ingestão). */
export default function SensorsHealthPage() {
  return <SensorsHealthClient />;
}
