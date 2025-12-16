import "@/styles/globals.css";
import type { Metadata } from "next";
import { AppToaster } from "@/components/app-toaster";

export const metadata: Metadata = {
  title: "AquaLink EQ",
  description: "Sistema de Monitoramento de ETA",
};

/**
 * Layout raiz da aplicação.
 * Envolve toda a aplicação com configurações globais como fontes, estilos e toasts.
 */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-br">
      <body className="antialiased">
        {children}
        <AppToaster />
      </body>
    </html>
  );
}
