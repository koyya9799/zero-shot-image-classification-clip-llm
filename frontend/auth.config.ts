import type { NextRequest } from "next/server"

// Edge-safe auth config for middleware (no OAuth providers)
export const authConfig = {
  providers: [], // Providers added in auth.ts to avoid edge runtime issues
  pages: {
    signIn: "/",
  },
  callbacks: {
    authorized({ auth, request }: { auth: any; request: NextRequest }) {
      const { nextUrl } = request
      const isLoggedIn = !!auth?.user
      const isOnProtected = 
        nextUrl.pathname.startsWith("/home") ||
        nextUrl.pathname.startsWith("/upload") ||
        nextUrl.pathname.startsWith("/evaluate")
      
      if (isOnProtected && !isLoggedIn) {
        return false // Redirect to sign-in page
      }
      
      return true
    },
  },
} as any

