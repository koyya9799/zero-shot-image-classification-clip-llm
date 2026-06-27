// Custom type declarations for next-auth v5 beta
declare module 'next-auth' {
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
      [key: string]: any
    }
  }

  // NextAuth is callable and returns handlers, auth, signIn, signOut
  function NextAuth(config: any): {
    handlers: { GET: any; POST: any }
    auth: (...args: any[]) => any
    signIn: (provider?: string, options?: any) => Promise<any>
    signOut: (options?: any) => Promise<void>
  }

  export default NextAuth
}

declare module 'next-auth/react' {
  export function SessionProvider(props: any): React.JSX.Element
  export function useSession(): any
  export function signIn(provider?: string, options?: any): Promise<any>
  export function signOut(options?: any): Promise<void>
}


