<script setup lang="ts">
import { ref } from 'vue'
import { useAppStore, API_BASE } from '@/stores/appStore'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Download } from 'lucide-vue-next'
import { toast } from 'vue-sonner'

const store = useAppStore()

const orientation = ref('horizontal')
const exportType = ref('normal')
const pharmacyLabel = ref('names')

function handleExportCsv() {
  toast.success('Downloading schedule CSV...')
  window.open(`${API_BASE}/schedules/${store.settings.year}/export?orientation=${orientation.value}&type=${exportType.value}&pharmacy_label=${pharmacyLabel.value}`, '_blank')
  store.isExportOpen = false
}

function handleExportPng() {
  toast.success('Downloading schedule PNG...')
  window.open(`${API_BASE}/schedules/${store.settings.year}/export?format=png&orientation=${orientation.value}&type=${exportType.value}&pharmacy_label=${pharmacyLabel.value}`, '_blank')
  store.isExportOpen = false
}
</script>

<template>
  <Dialog v-model:open="store.isExportOpen">
    <DialogContent class="max-w-md border-border/40">
      <DialogHeader>
        <DialogTitle class="flex items-center gap-2 text-base">
          <Download class="h-5 w-5 text-primary" />
          Export
        </DialogTitle>
      </DialogHeader>

      <div class="space-y-4 py-3">
        <!-- Orientation -->
        <div class="flex items-center justify-between p-3 rounded-lg border border-border/40 bg-card">
          <Label class="text-xs font-medium">Orientation</Label>
          <Select v-model="orientation">
            <SelectTrigger class="h-8 text-xs w-36">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="horizontal">horizontal</SelectItem>
              <SelectItem value="vertical">vertical</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <!-- Type -->
        <div class="flex items-center justify-between p-3 rounded-lg border border-border/40 bg-card">
          <Label class="text-xs font-medium">Type</Label>
          <Select v-model="exportType">
            <SelectTrigger class="h-8 text-xs w-36">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="tiny">tiny</SelectItem>
              <SelectItem value="compact">compact</SelectItem>
              <SelectItem value="normal">normal</SelectItem>
              <SelectItem value="extended">extended</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <!-- Pharmacy Labels (Names vs IDs) -->
        <div class="flex items-center justify-between p-3 rounded-lg border border-border/40 bg-card">
          <Label class="text-xs font-medium">Pharmacy Labels</Label>
          <Select v-model="pharmacyLabel">
            <SelectTrigger class="h-8 text-xs w-36">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="names">names</SelectItem>
              <SelectItem value="ids">ids</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <DialogFooter class="flex items-center justify-end gap-2 pt-2">
        <Button variant="destructive" size="sm" @click="store.isExportOpen = false">
          Cancel
        </Button>
        <Button variant="outline" size="sm" class="gap-1.5 border-border/40" @click="handleExportPng">
          <Download class="h-3.5 w-3.5" />
          Export png
        </Button>
        <Button size="sm" class="gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold" @click="handleExportCsv">
          <Download class="h-3.5 w-3.5" />
          Export csv
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
