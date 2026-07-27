<script setup lang="ts">
import { ref } from 'vue'
import { useAppStore } from '@/stores/appStore'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import FestivitiesTable from '@/components/FestivitiesTable.vue'
import PreferencesTable from '@/components/PreferencesTable.vue'
import DayMonthPicker from '@/components/DayMonthPicker.vue'
import { RefreshCw, Loader2, ChevronUp, ChevronDown } from 'lucide-vue-next'

const store = useAppStore()
const dateValue = ref(store.settings.regenerate_from || '')

function incrementYear() {
  store.updateSettings({ year: store.settings.year + 1 })
}

function decrementYear() {
  store.updateSettings({ year: store.settings.year - 1 })
}

function incrementTimeLimit() {
  store.updateSettings({ time_limit: store.settings.time_limit + 10 })
}

function decrementTimeLimit() {
  if (store.settings.time_limit > 10) {
    store.updateSettings({ time_limit: store.settings.time_limit - 10 })
  }
}

function handleConfirmReschedule() {
  if (dateValue.value) {
    store.updateSettings({ regenerate_from: dateValue.value })
  }
  store.isRescheduleOpen = false
  store.triggerGenerate()
}
</script>

<template>
  <Dialog v-model:open="store.isRescheduleOpen">
    <DialogContent class="max-w-3xl max-h-[90vh] flex flex-col p-0 gap-0 border-border/40">
      <DialogHeader class="p-6 pb-4">
        <DialogTitle class="flex items-center gap-2 text-lg">
          <RefreshCw class="h-5 w-5 text-primary" />
          Regenerate Schedule
        </DialogTitle>
      </DialogHeader>

      <Separator class="bg-border/30" />

      <ScrollArea class="flex-1 p-6 space-y-6 overflow-y-auto">
        <!-- Controls Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Year Selector -->
          <div class="flex items-center justify-between p-3 rounded-lg border border-border/40 bg-card">
            <Label class="text-xs font-medium">Year</Label>
            <div class="flex items-center space-x-2">
              <span class="font-bold text-sm text-primary font-mono">{{ store.settings.year }}</span>
              <div class="flex flex-col gap-0.5">
                <Button variant="ghost" size="icon" class="h-5 w-5" @click="incrementYear">
                  <ChevronUp class="h-3 w-3" />
                </Button>
                <Button variant="ghost" size="icon" class="h-5 w-5" @click="decrementYear">
                  <ChevronDown class="h-3 w-3" />
                </Button>
              </div>
            </div>
          </div>

          <!-- Use Previous Year Switch -->
          <div class="flex items-center justify-between p-3 rounded-lg border border-border/40 bg-card">
            <Label for="regen-use-prev-year" class="text-xs font-medium cursor-pointer">Use previous year</Label>
            <Switch
              id="regen-use-prev-year"
              :checked="store.settings.use_previous_year"
              @update:checked="(val: boolean) => store.updateSettings({ use_previous_year: val })"
            />
          </div>

          <!-- First Day of Week -->
          <div class="flex items-center justify-between p-3 rounded-lg border border-border/40 bg-card">
            <Label class="text-xs font-medium">First day of week</Label>
            <Select 
              :model-value="store.settings.first_day_of_week"
              @update:model-value="(val: any) => store.updateSettings({ first_day_of_week: String(val) })"
            >
              <SelectTrigger class="h-8 text-xs w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="sunday">sunday</SelectItem>
                <SelectItem value="monday">monday</SelectItem>
                <SelectItem value="saturday">saturday</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <!-- Auto Festivities Switch -->
          <div class="flex items-center justify-between p-3 rounded-lg border border-border/40 bg-card">
            <Label for="regen-auto-fest" class="text-xs font-medium cursor-pointer">Auto festivities</Label>
            <Switch
              id="regen-auto-fest"
              :checked="store.settings.auto_festivities"
              @update:checked="(val: boolean) => store.updateSettings({ auto_festivities: val })"
            />
          </div>

          <!-- Time Limit -->
          <div class="flex items-center justify-between p-3 rounded-lg border border-border/40 bg-card">
            <Label class="text-xs font-medium">Time Limit (sec)</Label>
            <div class="flex items-center space-x-2">
              <span class="font-bold text-sm text-primary font-mono">{{ store.settings.time_limit }}</span>
              <div class="flex flex-col gap-0.5">
                <Button variant="ghost" size="icon" class="h-5 w-5" @click="incrementTimeLimit">
                  <ChevronUp class="h-3 w-3" />
                </Button>
                <Button variant="ghost" size="icon" class="h-5 w-5" @click="decrementTimeLimit">
                  <ChevronDown class="h-3 w-3" />
                </Button>
              </div>
            </div>
          </div>

          <!-- Regenerate From Date -->
          <div class="flex items-center justify-between p-3 rounded-lg border border-border/40 bg-card">
            <Label class="text-xs font-medium">Regenerate from</Label>
            <DayMonthPicker 
              v-model="dateValue" 
              placeholder="gg/mm"
              class="w-36"
            />
          </div>
        </div>

        <!-- Space replacing middle separator -->
        <div class="h-4"></div>

        <!-- Sub Tables: Festivities & Preferences -->
        <div class="space-y-6">
          <FestivitiesTable />
          <PreferencesTable />
        </div>
      </ScrollArea>

      <Separator class="bg-border/30" />

      <DialogFooter class="p-4 gap-2">
        <Button variant="destructive" size="sm" @click="store.isRescheduleOpen = false">
          Cancel
        </Button>
        <Button 
          size="sm" 
          :disabled="store.isJobRunning"
          @click="handleConfirmReschedule"
          class="gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold"
        >
          <Loader2 v-if="store.isJobRunning" class="h-4 w-4 animate-spin" />
          <span>{{ store.isJobRunning ? 'Rescheduling...' : 'Generate' }}</span>
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
