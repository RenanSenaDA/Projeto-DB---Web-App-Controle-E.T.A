import SectionLabel from "../label-section";

interface KPISectionProps {
  color?: string;
  title_section?: string;
  children: React.ReactNode;
}

export default function KPISection({
  color = "bg-slate-300",
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
