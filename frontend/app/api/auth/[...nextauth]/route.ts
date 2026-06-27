import { handlers } from "@/auth"

// Force Node.js runtime to avoid edge runtime issues with openid-client
export const runtime = 'nodejs'

export const { GET, POST } = handlers
