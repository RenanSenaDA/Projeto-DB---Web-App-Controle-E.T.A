"use client";

import { Suspense } from "react";
import {
  Card,
  CardHeader,
  CardContent,
  CardTitle,
  CardDescription,
} from "@/ui/card";
import Image from "next/image";
import { RegisterForm } from "@/components/forms/register-form";
import { useRegisterViewModel } from "@/hooks/view/use-register-view-model";
import { ModeToggle } from "@/components/mode-toggle";
import Loading from "@/components/feedback/loading";

export default function RegisterPage() {
  const vm = useRegisterViewModel();

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted p-4 relative">
      <div className="absolute top-4 right-4">
        <ModeToggle />
      </div>
      <Card className="w-full max-w-md shadow-md">
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
          <CardTitle className="text-xl font-semibold">
            Finalizar Cadastro
          </CardTitle>
          <CardDescription>
            Defina sua senha para acessar o sistema
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Suspense fallback={<Loading />}>
            <RegisterForm
              email={vm.email}
              name={vm.name}
              onNameChange={vm.setName}
              password={vm.password}
              onPasswordChange={vm.setPassword}
              confirmPassword={vm.confirmPassword}
              onConfirmPasswordChange={vm.setConfirmPassword}
              onSubmit={vm.handleSubmit}
              submitting={vm.submitting}
              validToken={vm.validToken}
              onNavigateToLogin={vm.navigateToLogin}
              initializing={vm.initializing}
            />
          </Suspense>
        </CardContent>
      </Card>
    </div>
  );
}
