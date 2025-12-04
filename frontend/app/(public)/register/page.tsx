"use client";

import { useMemo, useState } from "react";
import { toast } from "sonner";
import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { Input } from "@/ui/input";
import { Button } from "@/ui/button";
import { Card, CardHeader, CardContent, CardTitle } from "@/ui/card";
import useAuth from "@/hooks/use-auth";

export default function RegisterPage() {
  const router = useRouter();
  const { register, loading } = useAuth();

  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  

  const isValidEmail = useMemo(() => {
    if (!email) return false;
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }, [email]);

  const isStrongPassword = useMemo(() => {
    if (!senha) return false;
    const hasUpper = /[A-Z]/.test(senha);
    const hasLower = /[a-z]/.test(senha);
    const hasDigit = /\d/.test(senha);
    const hasSpecial = /[^A-Za-z0-9]/.test(senha);
    const longEnough = senha.length >= 8;
    return hasUpper && hasLower && hasDigit && hasSpecial && longEnough;
  }, [senha]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nome || !email || !senha) return;
    if (!isValidEmail) {
      toast.error("E-mail inválido");
      return;
    }
    if (!isStrongPassword) {
      toast.error("Senha fraca. Use 8+ caracteres com maiúscula, minúscula, número e símbolo.");
      return;
    }
    try {
      await register(nome, email, senha);
      router.push("/login?registered=1");
    } catch {}
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100 p-4">
      <Card className="w-full max-w-sm shadow-md">
        <CardHeader className="flex flex-col items-center gap-3">
          <Image
            src="/aqualink-logo-escuro.svg"
            alt="Logo"
            width={128}
            height={128}
            priority
          />
          <CardTitle className="text-xl font-semibold">Criar conta</CardTitle>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              type="text"
              placeholder="Nome completo"
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              required
            />

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
            <p className="text-xs text-center text-slate-500">
              A senha deve ter 8+ caracteres e incluir pelo menos: 1 letra
              maiúscula, 1 letra minúscula, 1 número e 1 símbolo.
            </p>

            <Button
              type="submit"
              className="w-full bg-[#00283F]"
              disabled={loading || !isValidEmail || !isStrongPassword}
            >
              Registrar
            </Button>
          </form>

          <p className="text-sm text-center text-gray-600 mt-4">
            Já tem conta?{" "}
            <Link
              href="/login"
              className="text-[#00B4F0] underline hover:opacity-80"
            >
              Entrar
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
