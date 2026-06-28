import { SidebarProvider } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/AppSidebar"
import { TopNav } from "@/components/TopNav"

export default function UploadLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
      <SidebarProvider>
        <AppSidebar />
        <main className="flex-1 flex flex-col">
          <TopNav />
          <div className="flex-1">
            {children}
          </div>
        </main>
      </SidebarProvider>
  )
}
