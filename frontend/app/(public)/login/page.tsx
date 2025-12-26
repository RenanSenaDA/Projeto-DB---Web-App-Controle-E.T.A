"use client";

import { Suspense } from "react";
import Image from "next/image";
import { Card, CardHeader, CardContent, CardTitle } from "@/ui/card";
import { ModeToggle } from "@/components/mode-toggle";
import Loading from "@/components/feedback/loading";
import { LoginForm } from "@/components/forms/login-form";
import { useLoginViewModel } from "@/hooks/view/use-login-view-model";

/**
 * Página de Login.
 * Compõe a interface utilizando o ViewModel e o componente de formulário.
 */
export default function LoginPage() {
  const vm = useLoginViewModel();

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
            <h1 className="mt-2 text-[10px] font-bold tracking-widest dark:text-secondary-foreground uppercase opacity-70">
              Sistema de Monitoramento
            </h1>
          </div>

          <CardTitle className="text-xl font-semibold">Acessar conta</CardTitle>
        </CardHeader>

        <CardContent>
          <Suspense fallback={<Loading />}>
            <LoginForm 
              email={vm.email}
              onEmailChange={vm.setEmail}
              password={vm.password}
              onPasswordChange={vm.setPassword}
              onSubmit={vm.handleSubmit}
              loading={vm.loading}
              isValidEmail={vm.isValidEmail}
            />
          </Suspense>
        </CardContent>
      </Card>
    </div>
  );
}