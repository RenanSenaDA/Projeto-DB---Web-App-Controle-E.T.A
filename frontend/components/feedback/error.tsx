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
    <div className="flex h-screen items-center justify-center">
      <div className="text-center space-y-4">
        <AlertCircle className="h-12 w-12 text-rose-500 mx-auto" />
        <h2 className="text-xl font-bold text-slate-800">
          Erro ao carregar dados
        </h2>
        <p className="text-slate-500">{error}</p>
        <button
          onClick={fetchData}
          className="text-blue-600 hover:underline font-medium"
        >
          Tentar novamente
        </button>
      </div>
    </div>
  );
}
