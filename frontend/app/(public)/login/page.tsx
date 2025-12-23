"use client";

import { useMemo, useState, useEffect, Suspense } from "react";
import { toast } from "sonner";
import Image from "next/image";
import { useRouter, useSearchParams } from "next/navigation";
import { Input } from "@/ui/input";
import { Button } from "@/ui/button";
import { Card, CardHeader, CardContent, CardTitle } from "@/ui/card";
import { useAuth } from "@/hooks/auth/use-auth";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, loading } = useAuth();

  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");

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
    if (!email || !senha) return;
    if (!isValidEmail) {
      toast.error("E-mail inválido");
      return;
    }
    try {
      await login(email, senha);
      router.push("/dashboard");
    } catch {}
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input
        type="email"
        placeholder="E-mail"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />

      <Input
        type="password"
        placeholder="Senha"
        value={senha}
        onChange={(e) => setSenha(e.target.value)}
        required
      />

      <Button
        type="submit"
        className="w-full bg-secondary"
        disabled={loading || !isValidEmail}
      >
        Entrar
      </Button>
    </form>
  );
}

/**
 * Página de Login.
 * Permite ao usuário autenticar-se no sistema usando e-mail e senha.
 * Utiliza o hook useAuth para gerenciar a requisição de login.
 */
export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-muted p-4">
      <Card className="w-full max-w-sm shadow-md">
        <CardHeader className="flex flex-col items-center gap-3">
          <Image
            src="/aqualink-logo-escuro.svg"
            alt="Logo"
            width={128}
            height={128}
            priority
          />

          <CardTitle className="text-xl font-semibold">Acessar conta</CardTitle>
        </CardHeader>

        <CardContent>
          <Suspense fallback={<div>Carregando...</div>}>
            <LoginForm />
          </Suspense>
        </CardContent>
      </Card>
    </div>
  );
}
