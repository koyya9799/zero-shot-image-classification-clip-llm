"use client"

import { ThemeToggle } from "@/components/theme-toggle"
import { SidebarTrigger } from "@/components/ui/sidebar"

export function TopNav() {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-black dark:border-white bg-white dark:bg-black">
      <div className="container flex h-16 items-center justify-between px-4">
        {/* Left side */}
        <div className="flex items-center gap-4">
          <SidebarTrigger />
          <div className="hidden sm:block">
            <h1 className="font-bold text-lg text-black dark:text-white whitespace-nowrap">
              CLIP-LLM · Zero-Shot Image Classification
            </h1>
          </div>
        </div>

        {/* Right side */}
        <ThemeToggle />
      </div>
    </header>
  )
}