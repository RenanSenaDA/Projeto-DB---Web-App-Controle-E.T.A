import { cn } from "@/lib/utils";

/**
 * Propriedades do Rótulo de Seção.
 */
interface SectionLabelProps {
  /** Texto do título */
  title: string;
  /** Classe de cor para o indicador lateral (ex: "bg-blue-500") */
  color: string;
  /** Classes adicionais para o título */
  titleClassName?: string;
}

/**
 * Componente de rótulo para separar seções visuais.
 * Exibe uma pequena barra colorida seguida do título.
 * 
 * @component
 */
export default function SectionLabel({ title, color, titleClassName = "" }: SectionLabelProps) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <div className={cn("w-1 h-5 rounded-full shadow-sm", color)} />

      <h3 className={cn("font-semibold tracking-tight", titleClassName || "text-foreground")}>{title}</h3>
    </div>
  );
}
