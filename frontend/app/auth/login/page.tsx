import { signInWithGoogle } from "./actions"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Sparkles } from "lucide-react"

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-white dark:bg-black p-4">
      <div className="w-full max-w-md">
        <Card className="shadow-lg border border-black dark:border-white bg-white dark:bg-black">
          <CardHeader className="space-y-3">
            <CardTitle className="text-center text-2xl text-black dark:text-white">
              Sign In
            </CardTitle>

            <CardDescription className="text-center text-gray-700 dark:text-gray-300">
              Continue to Zero-Shot Image Classification
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6">
            <form action={signInWithGoogle}>
              <Button
                type="submit"
                size="lg"
                className="w-full bg-black dark:bg-white text-white dark:text-black border border-black dark:border-white hover:bg-gray-800 dark:hover:bg-gray-200"
              >
                Sign in with Google
              </Button>
            </form>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-blue-200 dark:border-blue-800" />
              </div>

              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white dark:bg-black text-blue-600 dark:text-blue-400">
                  Information
                </span>
              </div>
            </div>

            <div className="space-y-3 text-sm text-gray-600 dark:text-gray-400">
              <div className="flex items-start gap-3 p-3 rounded-lg bg-blue-50 dark:bg-blue-950/30">
                <Sparkles className="h-4 w-4 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">
                    First time?
                  </p>
                  <p>
                    Just sign in with Google and your account will be created
                    automatically.
                  </p>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-purple-50 dark:bg-purple-900/30">
                <p className="text-xs text-purple-700 dark:text-purple-300">
                  By signing in, you agree to our terms of service and privacy
                  policy.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}