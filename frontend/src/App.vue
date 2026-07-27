<script setup lang="ts">
import { onMounted } from 'vue'
import { Toaster } from 'vue-sonner'
import { useAppStore } from '@/stores/appStore'
import ScheduleView from '@/components/ScheduleView.vue'
import SettingsDialog from '@/components/SettingsDialog.vue'
import GenerateDialog from '@/components/GenerateDialog.vue'
import RescheduleDialog from '@/components/RescheduleDialog.vue'
import ExportDialog from '@/components/ExportDialog.vue'
import { TooltipProvider } from '@/components/ui/tooltip'
import {
  SidebarProvider,
  Sidebar,
  SidebarHeader,
  SidebarContent,
  SidebarFooter,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarInset,
} from '@/components/ui/sidebar'
import { Calendar, Settings, Pill, Wifi, WifiOff } from 'lucide-vue-next'

const store = useAppStore()

onMounted(() => {
  store.fetchSettings()
})
</script>

<template>
  <TooltipProvider :delay-duration="150">
    <SidebarProvider class="h-screen w-screen overflow-hidden bg-background text-foreground">
      <div class="flex h-screen w-screen overflow-hidden">
        <!-- shadcn Left Sidebar with right border divider -->
        <Sidebar class="border-r border-border/40 bg-sidebar">
          <SidebarHeader class="p-4 border-b border-border/40">
            <div class="flex items-center space-x-2.5">
              <div class="w-8 h-8 rounded-lg bg-primary text-primary-foreground flex items-center justify-center font-bold">
                <Pill class="h-4 w-4" />
              </div>
              <div class="flex flex-col">
                <span class="text-sm font-bold tracking-tight text-sidebar-foreground">Pharmacy Solver</span>
                <span class="text-[10px] text-muted-foreground">ASP Schedule System</span>
              </div>
            </div>
          </SidebarHeader>

          <SidebarContent class="p-2 space-y-1">
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton 
                  is-active 
                  class="w-full justify-start gap-2 h-9 text-xs font-medium"
                >
                  <Calendar class="h-4 w-4" />
                  <span>Schedules</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarContent>

          <SidebarFooter class="p-3 border-t border-border/40 space-y-3">
            <!-- WebSocket Status Badge -->
            <div class="flex items-center space-x-2 px-2 py-1 text-xs text-muted-foreground">
              <Wifi v-if="store.wsStatus === 'OPEN'" class="h-3.5 w-3.5 text-emerald-500 animate-pulse" />
              <WifiOff v-else class="h-3.5 w-3.5 text-destructive" />
              <span class="text-[11px] font-medium">{{ store.wsStatus === 'OPEN' ? 'WS Connected' : 'Connecting...' }}</span>
            </div>

            <!-- Settings Button -->
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton 
                  class="w-full justify-start gap-2 h-9 text-xs font-medium"
                  @click="store.isSettingsOpen = true"
                >
                  <Settings class="h-4 w-4" />
                  <span>Settings</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarFooter>
        </Sidebar>

        <!-- Main Content Area: Takes ALL available space -->
        <SidebarInset class="flex-1 h-screen overflow-hidden flex flex-col bg-background p-6">
          <ScheduleView />
        </SidebarInset>
      </div>

      <!-- Toast Notification Container -->
      <Toaster position="bottom-right" theme="dark" richColors />

      <!-- Popup Dialog Overlays -->
      <SettingsDialog />
      <GenerateDialog />
      <RescheduleDialog />
      <ExportDialog />
    </SidebarProvider>
  </TooltipProvider>
</template>
