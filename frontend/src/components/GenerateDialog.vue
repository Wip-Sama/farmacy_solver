<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useAppStore } from '@/stores/appStore'
import type { CustomFestivity, PharmacyPreference } from '@/stores/appStore'
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
import { Play, Loader2, ChevronUp, ChevronDown, AlertTriangle } from 'lucide-vue-next'
import { toast } from 'vue-sonner'

const store = useAppStore()
const daysOfWeek = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

// Local run-specific temporary state (Requirement 1)
const runYear = ref(store.settings.year)
const runUsePreviousYear = ref(store.settings.use_previous_year)
const runFirstDayOfWeek = ref(store.settings.first_day_of_week)
const runAutoFestivities = ref(store.settings.auto_festivities)
const runTimeLimit = ref(store.settings.time_limit)
const runFestivities = ref<CustomFestivity[]>([])
const runPreferences = ref<PharmacyPreference[]>([])

watch(() => store.isGenerateOpen, (isOpen) => {
  if (isOpen) {
    runYear.value = store.settings.year
    runUsePreviousYear.value = store.settings.use_previous_year
    runFirstDayOfWeek.value = store.settings.first_day_of_week
    runAutoFestivities.value = store.settings.auto_festivities
    runTimeLimit.value = store.settings.time_limit
    runFestivities.value = JSON.parse(JSON.stringify(store.settings.custom_festivities))
    runPreferences.value = JSON.parse(JSON.stringify(store.settings.pharmacy_preferences))
  }
}, { immediate: true })

// Validation: When auto festivities is OFF, all festivities must have a valid date specified
const hasMissingFestivityDate = computed(() => {
  if (!runAutoFestivities.value) {
    return runFestivities.value.some(f => !f.date || f.date.trim() === '')
  }
  return false
})

function incrementYear() {
  runYear.value += 1
}

function decrementYear() {
  runYear.value -= 1
}

function incrementTimeLimit() {
  runTimeLimit.value += 10
}

function decrementTimeLimit() {
  if (runTimeLimit.value > 10) {
    runTimeLimit.value -= 10
  }
}

function handleConfirmGenerate() {
  if (hasMissingFestivityDate.value) {
    toast.error('Cannot generate schedule: When auto festivities is OFF, all festivities must have a valid date.')
    return
  }
  store.isGenerateOpen = false
  store.triggerGenerate({
    year: runYear.value,
    use_previous_year: runUsePreviousYear.value,
    first_day_of_week: runFirstDayOfWeek.value,
    auto_festivities: runAutoFestivities.value,
    time_limit: runTimeLimit.value,
    custom_festivities: runFestivities.value,
    pharmacy_preferences: runPreferences.value
  })
}
</script>

<template>
  <Dialog v-model:open="store.isGenerateOpen">
    <DialogContent class="max-w-3xl max-h-[90vh] flex flex-col p-0 gap-0 border-border/40">
      <DialogHeader class="p-6 pb-4">
        <DialogTitle class="flex items-center gap-2 text-lg">
          <Play class="h-5 w-5 text-primary" />
          Generate Schedule
        </DialogTitle>
      </DialogHeader>

      <Separator class="bg-border/30" />

      <ScrollArea class="flex-1 p-6 space-y-6 overflow-y-auto">
        <!-- Validation Warning Alert -->
        <div v-if="hasMissingFestivityDate" class="p-3 rounded-lg border border-amber-500/40 bg-amber-500/10 flex items-center gap-2.5 text-xs text-amber-500 font-medium">
          <AlertTriangle class="h-4 w-4 shrink-0" />
          <span>Auto festivities is OFF: Every custom festivity must have a valid date (gg/mm) specified before generating.</span>
        </div>

        <!-- Controls Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Year Selector -->
          <div class="flex items-center justify-between p-3 rounded-lg border border-border/40 bg-card">
            <Label class="text-xs font-medium">Year</Label>
            <div class="flex items-center space-x-2">
              <span class="font-bold text-sm text-primary font-mono">{{ runYear }}</span>
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
            <Label for="gen-use-prev-year" class="text-xs font-medium cursor-pointer">Use previous year</Label>
            <Switch
              id="gen-use-prev-year"
              :model-value="runUsePreviousYear"
              @update:model-value="(val: boolean) => runUsePreviousYear = val"
            />
          </div>

          <!-- First Day of Week -->
          <div class="flex items-center justify-between p-3 rounded-lg border border-border/40 bg-card">
            <Label class="text-xs font-medium">First day of week</Label>
            <Select 
              :model-value="runFirstDayOfWeek"
              @update:model-value="(val: any) => runFirstDayOfWeek = String(val)"
            >
              <SelectTrigger class="h-8 text-xs w-32 capitalize">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem v-for="d in daysOfWeek" :key="d" :value="d" class="capitalize">
                  {{ d }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <!-- Auto Festivities Switch -->
          <div class="flex items-center justify-between p-3 rounded-lg border border-border/40 bg-card">
            <Label for="gen-auto-fest" class="text-xs font-medium cursor-pointer">Auto festivities</Label>
            <Switch
              id="gen-auto-fest"
              :model-value="runAutoFestivities"
              @update:model-value="(val: boolean) => runAutoFestivities = val"
            />
          </div>

          <!-- Time Limit -->
          <div class="flex items-center justify-between p-3 rounded-lg border border-border/40 bg-card col-span-1 md:col-span-2">
            <Label class="text-xs font-medium">Time Limit (sec)</Label>
            <div class="flex items-center space-x-2">
              <span class="font-bold text-sm text-primary font-mono">{{ runTimeLimit }}</span>
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
        </div>

        <!-- Space replacing middle separator -->
        <div class="h-4"></div>

        <!-- Sub Tables bound to run-specific local state (Requirement 1 & 4) -->
        <div class="space-y-6">
          <FestivitiesTable v-model:items="runFestivities" :auto-festivities="runAutoFestivities" />
          <PreferencesTable v-model:items="runPreferences" />
        </div>
      </ScrollArea>

      <Separator class="bg-border/30" />

      <DialogFooter class="p-4 gap-2">
        <Button variant="destructive" size="sm" @click="store.isGenerateOpen = false">
          Cancel
        </Button>
        <Button 
          size="sm" 
          :disabled="store.isJobRunning || hasMissingFestivityDate"
          @click="handleConfirmGenerate"
          class="gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Loader2 v-if="store.isJobRunning" class="h-4 w-4 animate-spin" />
          <span>{{ store.isJobRunning ? 'Generating...' : 'Generate' }}</span>
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
