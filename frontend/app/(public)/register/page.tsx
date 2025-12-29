import { Suspense } from "react";
import Loading from "@/components/feedback/loading";
import RegisterClient from "./register-client";

export default function RegisterPage() {
  return (
    <Suspense fallback={<Loading />}>
      <RegisterClient />
    </Suspense>
  );
}
