"use client"

import { Upload, Home } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
} from "@/components/ui/sidebar"

const items = [
  {
    title: "Home",
    url: "/home",
    icon: Home,
  },
  {
    title: "Upload & Classify",
    url: "/upload",
    icon: Upload,
  },
]

export function AppSidebar() {
  const pathname = usePathname()

  return (
    <Sidebar>
      <SidebarHeader className="border-b border-sidebar-border">
        <div className="px-4 py-2">
          <div>
            <h1 className="font-bold text-lg">CLIP-LLM</h1>
            <p className="text-xs text-muted-foreground">Zero-Shot Image Classification</p>
          </div>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton 
                    asChild
                    isActive={pathname === item.url}
                  >
                    <Link href={item.url}>
                      <item.icon />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        
        <SidebarGroup>
          <SidebarGroupLabel>Framework Features</SidebarGroupLabel>
          <SidebarGroupContent>
            <div className="px-3 py-2 text-xs text-muted-foreground space-y-1">
              <p>✓ CLIP Visual Embeddings</p>
              <p>✓ Zero-Shot Classification</p>
              <p>✓ Domain Adaptation</p>
              <p>✓ LLM Reasoning</p>
              <p>✓ Auto-Tuning</p>
              <p>✓ Comprehensive Metrics</p>
            </div>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  )
}
