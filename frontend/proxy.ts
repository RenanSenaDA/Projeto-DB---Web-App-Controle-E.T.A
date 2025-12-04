import { NextResponse, type NextRequest } from "next/server";

const publicRoutes = [
  { path: "/", whenAuthenticated: "redirect" },
  { path: "/login", whenAuthenticated: "redirect" },
  { path: "/register", whenAuthenticated: "redirect" },
] as const;

const REDIRECT_WHEN_AUTHENTICATED_ROUTE = "/dashboard";
const REDIRECT_WHEN_NOT_AUTHENTICATED_ROUTE = "/login";

export default function proxy(request: NextRequest) {
  const path = request.nextUrl.pathname;
  const publicRoute = publicRoutes.find((route) => route.path === path);
  const authToken =
    request.cookies.get("auth_token") ||
    request.cookies.get("__Secure-auth_token");

  if (!authToken && publicRoute) {
    return NextResponse.next();
  }

  if (!authToken && !publicRoute) {
    const redirectUrl = new URL(REDIRECT_WHEN_NOT_AUTHENTICATED_ROUTE, request.url);
    return NextResponse.redirect(redirectUrl);
  }

  if (authToken && publicRoute && publicRoute.whenAuthenticated === "redirect") {
    const redirectUrl = new URL(REDIRECT_WHEN_AUTHENTICATED_ROUTE, request.url);
    return NextResponse.redirect(redirectUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    // Exclui API, assets internos e qualquer caminho com extensão (arquivos estáticos em /public)
    "/((?!api|_next/static|_next/image|favicon.ico|.*\\..*).*)",
  ],
};
