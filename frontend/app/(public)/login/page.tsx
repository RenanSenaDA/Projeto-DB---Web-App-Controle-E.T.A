"use client";

import { useMemo, useState } from "react";
import { toast } from "sonner";
import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { Input } from "@/ui/input";
import { Button } from "@/ui/button";
import { Card, CardHeader, CardContent, CardTitle } from "@/ui/card";
import useAuth from "@/hooks/auth/use-auth";

/**
 * Página de Login.
 * Permite ao usuário autenticar-se no sistema usando e-mail e senha.
 * Utiliza o hook useAuth para gerenciar a requisição de login.
 */
export default function LoginPage() {
  const router = useRouter();
  const { login, loading } = useAuth();

  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");

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

          <p className="text-sm text-center text-muted-foreground mt-4">
            Não tem conta?{" "}
            <Link
              href="/register"
              className="text-primary underline hover:opacity-80"
            >
              Criar conta
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
