import "@/styles/globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AquaLink EQ",
  description: "Sistema de Monitoramento de ETA",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-br">
      <body className="antialiased">{children}</body>
    </html>
  );
}
