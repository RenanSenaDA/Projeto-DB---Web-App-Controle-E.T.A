"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { Input } from "@/ui/input";
import { Button } from "@/ui/button";
import { Card, CardHeader, CardContent, CardTitle } from "@/ui/card";
import useAuth from "@/hooks/use-auth";

export default function LoginPage() {
  const router = useRouter();
  const { login, loading, error } = useAuth();

  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !senha) return;
    try {
      await login(email, senha);
      router.push("/dashboard");
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
              className="w-full bg-[#00283F]"
              disabled={loading}
            >
              Entrar
            </Button>
          </form>
          {error && <p className="text-red-600 text-sm mt-2">{error}</p>}

          <p className="text-sm text-center text-gray-600 mt-4">
            Não tem conta?{" "}
            <Link
              href="/register"
              className="text-[#00B4F0] underline hover:opacity-80"
            >
              Criar conta
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
