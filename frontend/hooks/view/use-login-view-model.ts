import { useState, useEffect, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { useAuth } from "@/hooks/auth/use-auth";

/**
 * ViewModel para a Página de Login.
 * Implementa o padrão MVVM separando a lógica de visualização dos componentes de UI.
 * * Responsabilidades:
 * - Gerenciar estado do formulário (email, senha)
 * - Lidar com lógica de validação (formato de email)
 * - Orquestrar o fluxo de login via useAuth
 * - Gerenciar feedback visual (toasts) e navegação
 */
export function useLoginViewModel() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, loading } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState(""); // Mapeado do 'senha' original

  // Efeito para feedback de cadastro realizado
  useEffect(() => {
    if (searchParams.get("registered") === "1") {
      toast.success("Conta criada com sucesso! Faça login para continuar.");
      // Limpar param da URL sem reload
      router.replace("/login");
    }
  }, [searchParams, router]);

  // Validação simples de formato de e-mail
  const isValidEmail = useMemo(() => {
    if (!email) return false;
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }, [email]);

  /**
   * Manipula o envio do formulário de login.
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    
    if (!isValidEmail) {
      toast.error("E-mail inválido");
      return;
    }

    try {
      await login(email, password);
      router.push("/dashboard");
    } catch {
      // O tratamento de erro específico geralmente é feito dentro do useAuth ou interceptors,
      // mas mantendo a estrutura original onde o catch estava vazio ou genérico.
    }
  };

  return {
    // State
    email,
    setEmail,
    password,
    setPassword,
    
    // Status / Computed
    loading,
    isValidEmail,

    // Actions
    handleSubmit,
  };
}