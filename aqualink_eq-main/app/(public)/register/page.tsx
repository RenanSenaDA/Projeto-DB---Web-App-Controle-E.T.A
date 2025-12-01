"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { Input } from "@/ui/input";
import { Button } from "@/ui/button";
import { Card, CardHeader, CardContent, CardTitle } from "@/ui/card";

export default function RegisterPage() {
  const router = useRouter();

  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nome || !email || !senha) return;
    router.push("/login");
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

            <Button type="submit" className="w-full bg-[#00283F]">
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
