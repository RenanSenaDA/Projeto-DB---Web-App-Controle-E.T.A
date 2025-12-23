import { AlertCircle } from "lucide-react";

/**
 * Propriedades do componente de Erro.
 */
interface ErrorProps {
  /** Mensagem de erro a ser exibida */
  error: string | null;
  /** Função para tentar carregar os dados novamente */
  fetchData: () => void;
}

/**
 * Componente de feedback de erro.
 * Exibe uma mensagem amigável e um botão para tentar novamente.
 * 
 * @component
 */
export default function Error({ error, fetchData }: ErrorProps) {
  return (
    <div className="flex h-screen items-center justify-center bg-background">
      <div className="text-center space-y-4">
        <AlertCircle className="h-12 w-12 text-destructive mx-auto" />
        <h2 className="text-xl font-bold text-foreground">
          Erro ao carregar dados
        </h2>
        <p className="text-muted-foreground">{error}</p>
        <button
          onClick={fetchData}
          className="text-primary hover:underline font-medium"
        >
          Tentar novamente
        </button>
      </div>
    </div>
  );
}
