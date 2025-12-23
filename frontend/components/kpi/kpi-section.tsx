import SectionLabel from "../label-section";

/**
 * Propriedades da Seção de KPI.
 */
interface KPISectionProps {
  /** Cor do indicador da seção (classe Tailwind) */
  color?: string;
  /** Título da seção */
  title_section?: string;
  /** Cards de KPI a serem renderizados */
  children: React.ReactNode;
}

/**
 * Componente de Seção para agrupar Cards de KPI.
 * Renderiza um rótulo de seção e seus filhos.
 * 
 * @component
 */
export default function KPISection({
  color = "bg-muted",
  title_section = "Seção",
  children,
}: KPISectionProps) {
  return (
    <section>
      <SectionLabel title={title_section} color={color} />

      {children}
    </section>
  );
}
