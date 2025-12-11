import { AlertCircle } from "lucide-react";

interface ErrorProps {
  error: string | null;
  fetchData: () => void;
}

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
