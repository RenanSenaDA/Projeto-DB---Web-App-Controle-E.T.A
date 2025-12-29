"use client";

import { Suspense } from "react";
import Image from "next/image";
import { Card, CardHeader, CardContent, CardTitle } from "@/ui/card";
import { ModeToggle } from "@/components/mode-toggle";
import Loading from "@/components/feedback/loading";
import { LoginForm } from "@/components/forms/login-form";
import { useLoginViewModel } from "@/hooks/view/use-login-view-model";

export default function LoginClient() {
  const vm = useLoginViewModel();

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted p-4 relative">
      <div className="absolute top-4 right-4">
        <ModeToggle />
      </div>
      <Card className="w-full max-w-sm shadow-md">
        <CardHeader className="flex flex-col items-center gap-3">
          {/* ... resto igual ... */}
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
