import Link from "next/link"
import { Button } from "@/components/ui/button"
import { PublicNav } from "@/components/PublicNav"

export default function LandingPage() {
  return (
    <>
      <PublicNav />

      <div className="min-h-[calc(100vh-64px)] flex items-center justify-center bg-white dark:bg-black">
        <div className="container mx-auto px-4 py-12 max-w-10xl text-center">
          <div className="space-y-8">

            {/* Main Title */}
            <h1 className="text-3xl lg:text-7xl font-bold leading-tight text-black dark:text-white">
              Zero-Shot Image Classification
              <br />
              via CLIP and Large Language Models
            </h1>

            {/* Get Started Button */}
            <div className="pt-8">
              <Link href="/home">
                <Button
                  size="lg"
                  className="bg-black dark:bg-white hover:bg-gray-800 dark:hover:bg-gray-200 text-white dark:text-black px-8 py-6 text-lg font-semibold shadow-lg hover:shadow-xl transition-all"
                >
                  Get Started
                </Button>
              </Link>
            </div>

          </div>
        </div>
      </div>
    </>
  )
}