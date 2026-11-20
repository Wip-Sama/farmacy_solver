<script setup lang="ts">
import { ref, watch } from 'vue'
import { useAppStore } from '@/stores/appStore'
import type { CustomFestivity, Pharmacy } from '@/stores/appStore'
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
import PharmaciesTable from '@/components/PharmaciesTable.vue'
import { Settings, ChevronUp, ChevronDown, Save } from 'lucide-vue-next'

const store = useAppStore()
const daysOfWeek = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

const draftUsePreviousYear = ref(store.settings.use_previous_year)
const draftFirstDayOfWeek = ref(store.settings.first_day_of_week)
const draftAutoFestivities = ref(store.settings.auto_festivities)
const draftTimeLimit = ref(store.settings.time_limit)
const draftPharmacies = ref<Pharmacy[]>([])
const draftFestivities = ref<CustomFestivity[]>([])

watch(
  () => store.isSettingsOpen,
  (isOpen) => {
    if (isOpen) {
      draftUsePreviousYear.value = store.settings.use_previous_year
      draftFirstDayOfWeek.value = store.settings.first_day_of_week
      draftAutoFestivities.value = store.settings.auto_festivities
      draftTimeLimit.value = store.settings.time_limit
      draftPharmacies.value = JSON.parse(JSON.stringify(store.settings.pharmacies))
      draftFestivities.value = JSON.parse(JSON.stringify(store.settings.custom_festivities))
    }
  },
  { immediate: true }
)

function incrementTimeLimit() {
  draftTimeLimit.value += 10
}

function decrementTimeLimit() {
  if (draftTimeLimit.value > 10) {
    draftTimeLimit.value -= 10
  }
}

async function handleSaveSettings() {
  const ok = await store.updateSettings(
    {
      use_previous_year: draftUsePreviousYear.value,
      first_day_of_week: draftFirstDayOfWeek.value,
      auto_festivities: draftAutoFestivities.value,
      time_limit: draftTimeLimit.value,
      pharmacies: draftPharmacies.value,
      custom_festivities: draftFestivities.value,
    },
    true
  )
  if (ok) {
    store.isSettingsOpen = false
  }
}
</script>

<template>
  <Dialog v-model:open="store.isSettingsOpen">
    <DialogContent class="max-w-3xl max-h-[90vh] flex flex-col p-0 gap-0 border-border/40">
      <DialogHeader class="p-6 pb-4">
        <DialogTitle class="flex items-center gap-2 text-lg">
          <Settings class="h-5 w-5 text-primary" />
          Settings
        </DialogTitle>
      </DialogHeader>

      <Separator class="bg-border/30" />

      <ScrollArea class="flex-1 p-6 space-y-6 overflow-y-auto">
        <FestivitiesTable
          v-model:items="draftFestivities"
          :auto-festivities="draftAutoFestivities"
        />

        <div class="h-4" />

        <PharmaciesTable v-model:items="draftPharmacies" />

        <div class="h-4" />

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="flex items-center justify-between p-3 rounded-lg border border-border/40 bg-card">
            <Label for="settings-use-prev-year" class="text-xs font-medium cursor-pointer">
              Use previous year
            </Label>
            <Switch
              id="settings-use-prev-year"
              :model-value="draftUsePreviousYear"
              @update:model-value="(val: boolean) => (draftUsePreviousYear = val)"
            />
          </div>

          <div class="flex items-center justify-between p-3 rounded-lg border border-border/40 bg-card">
            <Label class="text-xs font-medium">First day of week</Label>
            <Select
              :model-value="draftFirstDayOfWeek"
              @update:model-value="(val: any) => (draftFirstDayOfWeek = String(val))"
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

          <div class="flex items-center justify-between p-3 rounded-lg border border-border/40 bg-card">
            <Label for="settings-auto-fest" class="text-xs font-medium cursor-pointer">
              Auto festivities
            </Label>
            <Switch
              id="settings-auto-fest"
              :model-value="draftAutoFestivities"
              @update:model-value="(val: boolean) => (draftAutoFestivities = val)"
            />
          </div>

          <div class="flex items-center justify-between p-3 rounded-lg border border-border/40 bg-card">
            <Label class="text-xs font-medium">Calculation Time Limit (sec)</Label>
            <div class="flex items-center space-x-2">
              <span class="font-bold text-sm text-primary font-mono">{{ draftTimeLimit }}</span>
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
      </ScrollArea>

      <Separator class="bg-border/30" />

      <DialogFooter class="p-4 gap-2">
        <Button variant="outline" size="sm" @click="store.isSettingsOpen = false">
          Cancel
        </Button>
        <Button
          size="sm"
          class="gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold"
          @click="handleSaveSettings"
        >
          <Save class="h-4 w-4" />
          Save Settings
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
