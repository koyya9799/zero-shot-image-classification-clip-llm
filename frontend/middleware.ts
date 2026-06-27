import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Define protected routes
  const isOnProtected = 
    pathname.startsWith("/home") ||
    pathname.startsWith("/upload") ||
    pathname.startsWith("/evaluate")

  if (isOnProtected) {
    // Check for NextAuth session cookie
    const sessionToken = request.cookies.get("authjs.session-token")?.value ||
                        request.cookies.get("__Secure-authjs.session-token")?.value

    if (!sessionToken) {
      // Redirect to login if no session
      const loginUrl = new URL("/", request.url)
      return NextResponse.redirect(loginUrl)
    }
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/((?!api/auth|_next/static|_next/image|.*\\.png$).*)"],
}
