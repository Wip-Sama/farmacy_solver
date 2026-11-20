<script setup lang="ts">
import { onMounted } from 'vue'
import { Toaster } from 'vue-sonner'
import { useAppStore } from '@/stores/appStore'
import ScheduleView from '@/components/ScheduleView.vue'
import SettingsDialog from '@/components/SettingsDialog.vue'
import ScheduleJobDialog from '@/components/ScheduleJobDialog.vue'
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
import { Calendar, Settings, Pill } from 'lucide-vue-next'

const store = useAppStore()

onMounted(() => {
  store.fetchSettings()
})
</script>

<template>
  <TooltipProvider :delay-duration="150">
    <SidebarProvider class="h-screen w-screen overflow-hidden bg-background text-foreground">
      <div class="flex h-screen w-screen overflow-hidden">
        <Sidebar class="border-r border-border/40 bg-sidebar">
          <SidebarHeader class="p-4 border-b border-border/40">
            <div class="flex items-center space-x-2.5">
              <div
                class="w-8 h-8 rounded-lg bg-primary text-primary-foreground flex items-center justify-center font-bold"
              >
                <Pill class="h-4 w-4" />
              </div>
              <div class="flex flex-col">
                <span class="text-sm font-bold tracking-tight text-sidebar-foreground">
                  Pharmacy Solver
                </span>
                <span class="text-[10px] text-muted-foreground">Shift Management</span>
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

          <SidebarFooter class="p-3 border-t border-border/40">
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

        <SidebarInset class="flex-1 h-screen overflow-hidden flex flex-col bg-background p-6">
          <ScheduleView />
        </SidebarInset>
      </div>

      <Toaster position="bottom-right" theme="dark" richColors />

      <SettingsDialog />
      <ScheduleJobDialog />
      <ExportDialog />
    </SidebarProvider>
  </TooltipProvider>
</template>
