"use client";

import { useMemo, useState, useEffect, Suspense } from "react";
import { toast } from "sonner";
import Image from "next/image";
import { useRouter, useSearchParams } from "next/navigation";
import { Input } from "@/ui/input";
import { Button } from "@/ui/button";
import { Card, CardHeader, CardContent, CardTitle } from "@/ui/card";
import { useAuth } from "@/hooks/auth/use-auth";
import { ModeToggle } from "@/components/mode-toggle";
import Loading from "@/components/feedback/loading";

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
        className="w-full bg-primary dark:text-secondary"
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
    <div className="min-h-screen flex items-center justify-center bg-muted p-4 relative">
      <div className="absolute top-4 right-4">
        <ModeToggle />
      </div>
      <Card className="w-full max-w-sm shadow-md">
        <CardHeader className="flex flex-col items-center gap-3">
          <div className="flex flex-col items-center justify-center pt-2.5 mb-4">
            <Image
              src="/aqualink-logo-escuro.svg"
              alt="AquaLink Logo"
              width={120}
              height={40}
              priority
              className="dark:hidden"
            />
            <Image
              src="/aqualink-logo.svg"
              alt="AquaLink Logo"
              width={120}
              height={40}
              priority
              className="hidden dark:block"
            />
            <h1 className="mt-2 text-[10px] font-bold tracking-widest text-secondary-foreground uppercase opacity-70">
              Sistema de Monitoramento
            </h1>
          </div>

          <CardTitle className="text-xl font-semibold">Acessar conta</CardTitle>
        </CardHeader>

        <CardContent>
          <Suspense fallback={<Loading />}>
            <LoginForm />
          </Suspense>
        </CardContent>
      </Card>
    </div>
  );
}
