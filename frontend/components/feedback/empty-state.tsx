import { SearchX, LucideIcon } from "lucide-react";
import { Button } from "@/ui/button";
import { cn } from "@/lib/utils";

/**
 * Propriedades do componente de Estado Vazio.
 */
interface EmptyStateProps {
  /** Título principal da mensagem */
  title?: string;
  /** Descrição detalhada */
  description?: string;
  /** Ícone ilustrativo (padrão: SearchX) */
  icon?: LucideIcon;
  /** Texto do botão de ação opcional */
  actionLabel?: string;
  /** Callback acionado ao clicar no botão de ação */
  onAction?: () => void;
  /** Classes CSS adicionais */
  className?: string;
}

/**
 * Componente de visualização para quando não há dados a exibir.
 * Pode incluir um ícone, título, descrição e uma ação de recuperação.
 * 
 * @component
 */
export default function EmptyState({
  title = "Nenhum dado encontrado",
  description = "Não encontramos registros para esta visualização.",
  icon: Icon = SearchX,
  actionLabel,
  onAction,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-12 text-center rounded-lg border border-dashed border-slate-300 bg-slate-50/50",
        className
      )}
    >
      <div className="bg-slate-100 p-3 rounded-full mb-4">
        <Icon className="h-8 w-8 text-slate-400" />
      </div>
      <h3 className="text-lg font-medium text-slate-900 mb-1">{title}</h3>
      <p className="text-sm text-slate-500 max-w-sm mx-auto mb-4">
        {description}
      </p>
      {actionLabel && onAction && (
        <Button
          variant="outline"
          onClick={onAction}
          className="text-slate-600 border-slate-300 hover:bg-white"
        >
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
