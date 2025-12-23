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

export default function RegisterPage() {
  const vm = useRegisterViewModel();

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted p-4">
      <Card className="w-full max-w-md shadow-md">
        <CardHeader className="flex flex-col items-center gap-3">
          <Image
            src="/aqualink-logo-escuro.svg"
            alt="Logo"
            width={128}
            height={128}
            priority
          />
          <CardTitle className="text-xl font-semibold">
            Finalizar Cadastro
          </CardTitle>
          <CardDescription>
            Defina sua senha para acessar o sistema
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Suspense fallback={<div className="text-center">Carregando...</div>}>
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
