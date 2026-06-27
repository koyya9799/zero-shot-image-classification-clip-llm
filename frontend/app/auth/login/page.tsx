'use client'

import { signIn } from "@/auth"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Sparkles } from "lucide-react"

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-white dark:bg-black p-4">
      <div className="w-full max-w-md">
        <Card className="shadow-lg border border-black dark:border-white bg-white dark:bg-black">
          <CardHeader className="space-y-3">
            <CardTitle className="text-center text-2xl text-black dark:text-white">Sign In</CardTitle>
            <CardDescription className="text-center text-gray-700 dark:text-gray-300">
              Continue to Zero-Shot Image Classification
            </CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-6">
            <div className="space-y-3">
              <form
                action={async () => {
                  "use server"
                  await signIn("google", { redirectTo: "/home" })
                }}
              >
                <Button
                  type="submit"
                  size="lg"
                  className="w-full bg-black dark:bg-white text-white dark:text-black border border-black dark:border-white hover:bg-gray-800 dark:hover:bg-gray-200 transition-all font-semibold"
                >
                  <svg className="h-5 w-5 mr-2" viewBox="0 0 24 24">
                    <path
                      fill="currentColor"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="currentColor"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    />
                  </svg>
                  Sign in with Google
                </Button>
              </form>
            </div>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-blue-200 dark:border-blue-800"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white dark:bg-gray-900 text-blue-600 dark:text-blue-400">
                  Information
                </span>
              </div>
            </div>

            <div className="space-y-3 text-sm text-gray-600 dark:text-gray-400">
              <div className="flex items-start gap-3 p-3 rounded-lg bg-blue-50 dark:bg-blue-950/30">
                <Sparkles className="h-4 w-4 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">First time?</p>
                  <p>Just sign in with Google and your account will be created automatically</p>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-purple-50 dark:bg-purple-900/30">
                <p className="text-xs text-purple-700 dark:text-purple-300">
                  By signing in, you agree to our terms of service and privacy policy. Your Google account information is used only for authentication.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
