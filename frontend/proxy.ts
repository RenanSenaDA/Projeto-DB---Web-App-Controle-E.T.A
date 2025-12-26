/**
 * Middleware de Autenticação e Redirecionamento (Proxy).
 *
 * Intercepta requisições para controlar acesso às rotas
 * com base na presença do token de autenticação (cookies).
 *
 * Regras:
 * 1) Se NÃO tiver token e rota for pública -> permite
 * 2) Se NÃO tiver token e rota for privada -> redireciona p/ /login
 * 3) Se tiver token e rota for pública -> redireciona p/ /dashboard
 * 4) Se tiver token e rota for privada -> permite
 */

import { NextResponse, type NextRequest } from "next/server";

const publicRoutes = [
  { path: "/", whenAuthenticated: "redirect" },
  { path: "/login", whenAuthenticated: "redirect" },
] as const;

const REDIRECT_WHEN_AUTHENTICATED_ROUTE = "/dashboard";
const REDIRECT_WHEN_NOT_AUTHENTICATED_ROUTE = "/login";

export default function proxy(request: NextRequest) {
  const path = request.nextUrl.pathname;
  const publicRoute = publicRoutes.find((route) => route.path === path);
  const searchParams = request.nextUrl.searchParams;
  const token = searchParams.get("token");

  // Permite acesso à rota de registro se houver um token (convite)
  if (path === "/register" && token) {
    return NextResponse.next();
  }

  // Token via cookie (suporta variação "__Secure-")
  const authToken =
    request.cookies.get("auth_token") ||
    request.cookies.get("__Secure-auth_token");

  if (!authToken && publicRoute) {
    return NextResponse.next();
  }

  if (!authToken && !publicRoute) {
    const redirectUrl = new URL(
      REDIRECT_WHEN_NOT_AUTHENTICATED_ROUTE,
      request.url
    );
    return NextResponse.redirect(redirectUrl);
  }

  if (authToken && publicRoute && publicRoute.whenAuthenticated === "redirect") {
    const redirectUrl = new URL(
      REDIRECT_WHEN_AUTHENTICATED_ROUTE,
      request.url
    );
    return NextResponse.redirect(redirectUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!api|_next/static|_next/image|favicon.ico|.*\\..*).*)",
  ],
};

