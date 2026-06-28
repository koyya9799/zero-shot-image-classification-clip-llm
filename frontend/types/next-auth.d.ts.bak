// Custom type declarations for next-auth v5 beta

declare module "next-auth" {
  interface Session {
    user?: {
      id?: string
      name?: string | null
      email?: string | null
      image?: string | null
    }
  }

  interface User {
    id?: string
    name?: string | null
    email?: string | null
    image?: string | null
  }

  namespace NextAuth {
    interface NextAuthConfig {
      [key: string]: unknown
    }
  }

  function NextAuth(config: unknown): {
    handlers: {
      GET: unknown
      POST: unknown
    }
    auth: (...args: unknown[]) => unknown
    signIn: (
      provider?: string,
      options?: Record<string, unknown>
    ) => Promise<unknown>
    signOut: (
      options?: Record<string, unknown>
    ) => Promise<void>
  }

  export default NextAuth
}

declare module "next-auth/react" {
  export function SessionProvider(
    props: Record<string, unknown>
  ): React.JSX.Element

  export function useSession(): unknown

  export function signIn(
    provider?: string,
    options?: Record<string, unknown>
  ): Promise<unknown>

  export function signOut(
    options?: Record<string, unknown>
  ): Promise<void>
}