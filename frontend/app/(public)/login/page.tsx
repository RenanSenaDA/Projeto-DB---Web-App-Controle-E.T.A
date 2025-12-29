import { Suspense } from "react";
import Loading from "@/components/feedback/loading";
import LoginClient from "./login-client";

export default function LoginPage() {
  return (
    <Suspense fallback={<Loading />}>
      <LoginClient />
    </Suspense>
  );
}
