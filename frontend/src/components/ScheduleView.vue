<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  Plus, 
  Download, 
  RefreshCw, 
  Check, 
  Minus, 
  Loader2,
  Calendar
} from 'lucide-vue-next'

const store = useAppStore()

onMounted(() => {
  store.fetchAvailableYears()
  store.fetchScheduleRows(store.settings.year)
})

const displayPharmacies = computed(() => {
  if (store.settings.pharmacies && store.settings.pharmacies.length > 0) {
    return store.settings.pharmacies
  }
  return Array.from({ length: 10 }, (_, i) => ({ id: i + 1, name: `F${i + 1}`, location: 'centro' }))
})

function getPharmacyName(p: { id: number; name?: string }): string {
  const mapped = store.settings.pharmacies.find(item => item.id === p.id)
  if (mapped && mapped.name && mapped.name.trim() !== '') {
    return mapped.name
  }
  if (p.name && p.name.trim() !== '' && !p.name.startsWith('F')) {
    return p.name
  }
  return mapped?.name || p.name || `F${p.id}`
}

function handleYearChange(yr: number) {
  store.updateSettings({ year: yr })
  store.fetchScheduleRows(yr)
}

function toggleViewMode() {
  store.viewMode = store.viewMode === 'compact' ? 'extended' : 'compact'
  store.fetchScheduleRows(store.settings.year)
}

function checkSummer(row: any): boolean {
  if (row.is_summer !== undefined) {
    return row.is_summer
  }
  if (!row.date) return false
  try {
    const parts = row.date.split('-')
    if (parts.length >= 2) {
      const month = parseInt(parts[1], 10)
      return month >= 6 && month <= 8
    }
  } catch (e) {
    return false
  }
  return false
}

function getPharmacyColorClass(pharmacyId: number): { text: string; bg: string; border: string; pill: string } {
  const p = store.settings.pharmacies.find(item => item.id === pharmacyId)
  const loc = p?.location?.toLowerCase() || ''
  
  if (loc === 'centro') {
    return {
      text: 'text-blue-400 font-bold',
      bg: 'bg-blue-500/10',
      border: 'border-blue-500/30',
      pill: 'bg-blue-500/20 text-blue-300 border border-blue-500/30 font-semibold'
    }
  } else if (loc === 'marina') {
    return {
      text: 'text-teal-400 font-bold',
      bg: 'bg-teal-500/10',
      border: 'border-teal-500/30',
      pill: 'bg-teal-500/20 text-teal-300 border border-teal-500/30 font-semibold'
    }
  }
  
  const colors = [
    { text: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/30', pill: 'bg-blue-500/20 text-blue-300 border border-blue-500/30' },
    { text: 'text-teal-400', bg: 'bg-teal-500/10', border: 'border-teal-500/30', pill: 'bg-teal-500/20 text-teal-300 border border-teal-500/30' },
    { text: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/30', pill: 'bg-purple-500/20 text-purple-300 border border-purple-500/30' },
    { text: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/30', pill: 'bg-amber-500/20 text-amber-300 border border-amber-500/30' },
    { text: 'text-rose-400', bg: 'bg-rose-500/10', border: 'border-rose-500/30', pill: 'bg-rose-500/20 text-rose-300 border border-rose-500/30' }
  ]
  return colors[pharmacyId % colors.length]
}
</script>

<template>
  <div class="flex-1 flex flex-col h-full min-h-0 space-y-4">
    <!-- Action Bar -->
    <div class="flex items-center justify-between gap-4 shrink-0">
      <!-- Year Selector Dropdown (Generated Years Only) & View Toggle -->
      <div class="flex items-center space-x-3">
        <Select 
          :model-value="store.settings.year.toString()" 
          @update:model-value="(val: any) => handleYearChange(parseInt(val, 10))"
        >
          <SelectTrigger class="h-9 text-lg font-bold font-mono text-primary border-border/40 w-28">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem v-for="yr in store.availableYears" :key="yr" :value="yr.toString()">
              {{ yr }}
            </SelectItem>
          </SelectContent>
        </Select>

        <Button 
          variant="outline" 
          size="sm" 
          class="h-8 text-xs gap-1.5 border-border/40"
          @click="toggleViewMode"
        >
          <span class="text-muted-foreground">Compatto / Esteso:</span>
          <span class="font-bold uppercase text-primary">{{ store.viewMode }}</span>
        </Button>
      </div>

      <!-- Action Buttons with Tooltips: New Schedule (+), Export (↓), Regenerate (↺) -->
      <div class="flex items-center space-x-2">
        <!-- Tooltip: New Schedule -->
        <Tooltip>
          <TooltipTrigger as-child>
            <Button 
              variant="outline" 
              size="icon" 
              class="h-9 w-9 border-border/40"
              :disabled="store.isJobRunning"
              @click="store.isGenerateOpen = true"
            >
              <Plus class="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p class="text-xs">Generate New Schedule</p>
          </TooltipContent>
        </Tooltip>

        <!-- Tooltip: Export -->
        <Tooltip>
          <TooltipTrigger as-child>
            <Button 
              variant="outline" 
              size="icon" 
              class="h-9 w-9 border-border/40"
              @click="store.isExportOpen = true"
            >
              <Download class="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p class="text-xs">Export Schedule (PNG / CSV)</p>
          </TooltipContent>
        </Tooltip>

        <!-- Tooltip: Regenerate -->
        <Tooltip>
          <TooltipTrigger as-child>
            <Button 
              variant="outline" 
              size="icon" 
              class="h-9 w-9 border-border/40"
              :disabled="store.isJobRunning"
              @click="store.isRescheduleOpen = true"
            >
              <RefreshCw class="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p class="text-xs">Reschedule / Regenerate</p>
          </TooltipContent>
        </Tooltip>
      </div>
    </div>

    <Separator class="bg-border/30 shrink-0" />

    <!-- Schedule Data Grid (Fills 100% available space with Sticky Header) -->
    <div class="flex-1 min-h-0 rounded-md border border-border/40 bg-card overflow-y-auto overflow-x-auto relative">
      <Table no-wrapper class="w-full relative border-collapse">
        <!-- Sticky Header row that stays in view on scroll -->
        <TableHeader class="sticky top-0 z-30 bg-card shadow-sm border-b border-border/40">
          <TableRow v-if="store.viewMode === 'compact'" class="hover:bg-transparent">
            <TableHead class="sticky top-0 z-30 w-28 font-semibold bg-card border-b border-border/40 shadow-sm">Settimana</TableHead>
            <TableHead class="sticky top-0 z-30 w-36 font-semibold bg-card border-b border-border/40 shadow-sm">Data</TableHead>
            <TableHead class="sticky top-0 z-30 font-semibold bg-card border-b border-border/40 shadow-sm">Farmacia di Turno</TableHead>
            <TableHead class="sticky top-0 z-30 w-48 font-semibold bg-card border-b border-border/40 shadow-sm">Festività</TableHead>
          </TableRow>
          <TableRow v-else class="hover:bg-transparent">
            <TableHead class="sticky top-0 z-30 w-28 font-semibold bg-card border-b border-border/40 shadow-sm">Settimana</TableHead>
            <TableHead class="sticky top-0 z-30 w-36 font-semibold bg-card border-b border-border/40 shadow-sm">Data</TableHead>
            <TableHead 
              v-for="p in displayPharmacies" 
              :key="p.id" 
              class="sticky top-0 z-30 text-center font-semibold text-xs px-1.5 py-2 truncate min-w-[80px] bg-card border-b border-border/40 shadow-sm"
            >
              <span :class="['px-2 py-1 rounded-md text-[11px] tracking-wide inline-block', getPharmacyColorClass(p.id).pill]">
                {{ p.name || ('F' + p.id) }}
              </span>
            </TableHead>
            <TableHead class="sticky top-0 z-30 w-48 font-semibold bg-card border-b border-border/40 shadow-sm">Festività</TableHead>
          </TableRow>
        </TableHeader>
          <TableBody>
            <TableRow 
              v-for="row in store.scheduleRows" 
              :key="row.week"
              :class="[
                row.status === 'past' ? 'opacity-40 bg-muted/20' : '',
                row.status === 'current' ? 'bg-primary/10 border-l-4 border-l-primary font-semibold' : '',
                checkSummer(row) && row.status !== 'current' ? 'bg-amber-500/5 hover:bg-amber-500/10' : ''
              ]"
            >
              <!-- Settimana Column with Summer Highlight -->
              <TableCell class="font-bold text-xs font-mono">
                <span 
                  v-if="checkSummer(row)" 
                  class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] bg-amber-500/20 text-amber-400 border border-amber-500/30 font-bold"
                  title="Periodo Estivo (15 Giugno - 15 Settembre)"
                >
                  ☀️ Wk {{ row.week }}
                </span>
                <span v-else class="text-primary">
                  Wk {{ row.week }}
                </span>
              </TableCell>
              <TableCell class="text-xs font-mono text-muted-foreground">{{ row.date }}</TableCell>

              <!-- Compact View Column: Display mapped pharmacy name with Zone Color Pill -->
              <TableCell v-if="store.viewMode === 'compact'">
                <div class="flex flex-wrap gap-1.5">
                  <span 
                    v-for="p in row.pharmacies" 
                    :key="p.id"
                    :class="['px-2 py-0.5 rounded text-[11px] font-medium inline-block', getPharmacyColorClass(p.id).pill]"
                  >
                    {{ getPharmacyName(p) }} ({{ p.location }})
                  </span>
                </div>
              </TableCell>

              <!-- Extended View Columns: All Pharmacies (Names & IDs) -->
              <template v-else>
                <TableCell v-for="p in displayPharmacies" :key="p.id" class="text-center">
                  <Check v-if="row.pharmacies.some((pharm: any) => pharm.id === p.id)" class="h-4 w-4 mx-auto text-emerald-500 font-bold" />
                  <Minus v-else class="h-4 w-4 mx-auto text-muted-foreground/40" />
                </TableCell>
              </template>

              <TableCell class="text-xs text-amber-500 font-medium italic">
                {{ row.festivity || '-' }}
              </TableCell>
            </TableRow>

            <TableRow v-if="store.scheduleRows.length === 0">
              <TableCell :colspan="store.viewMode === 'compact' ? 4 : (displayPharmacies.length + 3)" class="text-center py-20 text-muted-foreground italic text-xs">
                <div class="flex flex-col items-center gap-2">
                  <Calendar class="h-8 w-8 text-muted-foreground/40" />
                  <span>No schedule data generated yet for {{ store.settings.year }}. Click + Generate above to start solving.</span>
                </div>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
    </div>

    <!-- Italian visual indicators legend Footer -->
    <div class="flex items-center justify-between gap-4 shrink-0 pt-1">
      <div class="flex items-center space-x-4 text-xs text-muted-foreground">
        <span class="flex items-center space-x-1.5"><span class="w-2.5 h-2.5 rounded-full bg-muted-foreground/40"></span> Settimane passate</span>
        <span class="flex items-center space-x-1.5"><span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Questa settimana</span>
        <span class="flex items-center space-x-1.5"><span class="w-2.5 h-2.5 rounded-full bg-primary"></span> Prossime settimane</span>
        <span class="flex items-center space-x-1.5"><span class="w-2.5 h-2.5 rounded-full bg-amber-400"></span> ☀️ Periodo estivo (15 Giugno - 15 Settembre)</span>
      </div>
    </div>

    <!-- Live Clingo Solver Progress Dialog -->
    <Dialog v-model:open="store.isProgressModalOpen">
      <DialogContent class="max-w-2xl bg-card border-border/40">
        <DialogHeader>
          <DialogTitle class="flex items-center gap-2 text-base">
            <Loader2 class="h-4 w-4 animate-spin text-primary" />
            Live ASP Solver Execution (Clingo)
          </DialogTitle>
        </DialogHeader>

        <!-- Log Viewer Container -->
        <ScrollArea class="h-64 rounded-md border border-border/40 bg-black p-4 font-mono text-xs text-emerald-400">
          <div v-for="(line, idx) in store.jobProgressLines" :key="idx" class="leading-relaxed">
            {{ line }}
          </div>
          <div v-if="store.isJobRunning" class="text-primary animate-pulse pt-2 flex items-center gap-2">
            <Loader2 class="h-3.5 w-3.5 animate-spin" />
            <span>Solving answer sets in background...</span>
          </div>
        </ScrollArea>

        <DialogFooter>
          <Button variant="outline" size="sm" @click="store.isProgressModalOpen = false">
            Close Log View
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
