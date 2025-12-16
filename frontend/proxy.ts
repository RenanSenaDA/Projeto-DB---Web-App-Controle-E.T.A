/**
 * Middleware de Autenticação e Redirecionamento (Proxy).
 *
 * Este arquivo intercepta as requisições para controlar o acesso às rotas
 * com base na presença do token de autenticação (cookies).
 *
 * Funcionalidades:
 * 1. Protege rotas privadas redirecionando para login.
 * 2. Redireciona usuários logados para fora de páginas públicas (login/register).
 */

import { NextResponse, type NextRequest } from "next/server";

/**
 * Lista de rotas públicas acessíveis sem autenticação.
 * @property path - O caminho da rota.
 * @property whenAuthenticated - Ação a tomar se o usuário já estiver logado ('redirect' = manda para dashboard).
 */
const publicRoutes = [
  { path: "/", whenAuthenticated: "redirect" },
  { path: "/login", whenAuthenticated: "redirect" },
  { path: "/register", whenAuthenticated: "redirect" },
] as const;

/** Rota de destino para usuários autenticados que tentam acessar páginas públicas */
const REDIRECT_WHEN_AUTHENTICATED_ROUTE = "/dashboard";

/** Rota de login para redirecionar usuários não autenticados */
const REDIRECT_WHEN_NOT_AUTHENTICATED_ROUTE = "/login";

/**
 * Função principal do Middleware.
 * Executa a lógica de verificação de token e decisão de redirecionamento.
 *
 * @param request - A requisição Next.js recebida.
 */
export default function proxy(request: NextRequest) {
  const path = request.nextUrl.pathname;
  const publicRoute = publicRoutes.find((route) => route.path === path);

  // Verifica presença do token em cookies (suporta nome padrão e seguro)
  const authToken =
    request.cookies.get("auth_token") ||
    request.cookies.get("__Secure-auth_token");

  // CASO 1: Usuário não logado acessando rota pública -> Permite
  if (!authToken && publicRoute) {
    return NextResponse.next();
  }

  // CASO 2: Usuário não logado acessando rota privada -> Redireciona para Login
  if (!authToken && !publicRoute) {
    const redirectUrl = new URL(REDIRECT_WHEN_NOT_AUTHENTICATED_ROUTE, request.url);
    return NextResponse.redirect(redirectUrl);
  }

  // CASO 3: Usuário logado acessando rota pública (ex: login) -> Redireciona para Dashboard
  if (authToken && publicRoute && publicRoute.whenAuthenticated === "redirect") {
    const redirectUrl = new URL(REDIRECT_WHEN_AUTHENTICATED_ROUTE, request.url);
    return NextResponse.redirect(redirectUrl);
  }

  // CASO 4: Usuário logado acessando rota privada -> Permite
  return NextResponse.next();
}

/**
 * Configuração do Matcher do Middleware.
 * Define quais caminhos devem passar por este middleware.
 */
export const config = {
  matcher: [
    // Exclui rotas de API, arquivos estáticos (_next/static, _next/image, favicon)
    // e arquivos com extensão (ex: .css, .js, .svg) para evitar processamento desnecessário
    "/((?!api|_next/static|_next/image|favicon.ico|.*\\..*).*)",
  ],
};
