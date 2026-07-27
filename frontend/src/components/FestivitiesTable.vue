<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAppStore } from '@/stores/appStore'
import type { CustomFestivity } from '@/stores/appStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import DayMonthPicker from '@/components/DayMonthPicker.vue'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Plus, Trash2 } from 'lucide-vue-next'

const props = defineProps<{
  items?: CustomFestivity[]
  autoFestivities?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:items', val: CustomFestivity[]): void
}>()

const store = useAppStore()

const list = computed<CustomFestivity[]>(() => {
  return props.items !== undefined ? props.items : store.settings.custom_festivities
})

const isAutoFest = computed<boolean>(() => {
  return props.autoFestivities !== undefined ? props.autoFestivities : store.settings.auto_festivities
})

const newName = ref('')
const newDate = ref('')

function updateList(newList: CustomFestivity[]) {
  if (props.items !== undefined) {
    emit('update:items', newList)
  } else {
    store.updateSettings({ custom_festivities: newList })
  }
}

function addFestivity() {
  if (!newName.value.trim()) return
  const updated = [...list.value, { name: newName.value.trim(), date: newDate.value }]
  updateList(updated)
  newName.value = ''
  newDate.value = ''
}

function updateFestivity(index: number, name: string, date: string) {
  const updated = [...list.value]
  updated[index] = { name, date }
  updateList(updated)
}

function removeFestivity(index: number) {
  const updated = list.value.filter((_: unknown, i: number) => i !== index)
  updateList(updated)
}
</script>

<template>
  <div class="space-y-3">
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-semibold text-foreground">Festivities</h3>
      <span v-if="!isAutoFest" class="text-xs text-amber-500 font-medium italic">
        (Auto festivities OFF - Manual dates required)
      </span>
    </div>

    <!-- Explanation note from wireframe -->
    <p class="text-xs text-muted-foreground italic leading-relaxed">
      Questo blocco appare quando le festività automatiche sono disattivate. Permette di inserire o modificare festività personalizzate (es. Pasqua, Natale, Capodanno).
    </p>

    <!-- Table -->
    <div class="rounded-md border border-border/40 overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow class="hover:bg-transparent border-b border-border/40">
            <TableHead class="font-semibold text-muted-foreground">Name</TableHead>
            <TableHead class="w-40 font-semibold text-muted-foreground">Date (gg/mm)</TableHead>
            <TableHead class="text-right w-16 font-semibold text-muted-foreground">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow 
            v-for="(fest, index) in list" 
            :key="index" 
            :class="[
              'border-b border-border/40 transition-colors',
              !isAutoFest && (!fest.date || !fest.date.trim()) 
                ? 'bg-red-500/5 hover:bg-red-500/10' 
                : ''
            ]"
          >
            <TableCell class="p-1.5">
              <Input 
                :model-value="fest.name"
                @change="(e: Event) => updateFestivity(index, (e.target as HTMLInputElement).value, fest.date)"
                placeholder="Festivity Name"
                class="h-8 text-xs bg-transparent border-transparent hover:border-border/40 focus:border-primary"
              />
            </TableCell>
            <TableCell class="p-1.5">
              <DayMonthPicker 
                :model-value="fest.date" 
                @update:model-value="(val: string) => updateFestivity(index, fest.name, val)"
                :class="[
                  'w-36 transition-colors',
                  !isAutoFest && (!fest.date || !fest.date.trim())
                    ? 'border-red-500 bg-red-500/10 text-red-400 dark:border-red-500 dark:bg-red-950/40 dark:text-red-400 ring-1 ring-red-500/50 font-medium'
                    : ''
                ]"
              />
            </TableCell>
            <TableCell class="text-right p-1.5">
              <Button 
                variant="ghost" 
                size="icon" 
                class="h-7 w-7 text-destructive hover:text-destructive hover:bg-destructive/10"
                @click="removeFestivity(index)"
              >
                <Trash2 class="h-3.5 w-3.5" />
              </Button>
            </TableCell>
          </TableRow>
          <TableRow v-if="list.length === 0">
            <TableCell colspan="3" class="text-center text-xs text-muted-foreground italic py-4">
              No custom festivities added.
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </div>

    <!-- Add Row Form (Date optional) -->
    <div class="flex items-center gap-2 pt-1">
      <Input 
        v-model="newName" 
        placeholder="Festivity Name (e.g. Pasqua)" 
        class="h-8 text-xs flex-1 border-border/40"
        @keyup.enter="addFestivity"
      />
      <DayMonthPicker 
        v-model="newDate" 
        placeholder="gg/mm"
        class="w-36"
      />
      <Button size="sm" variant="secondary" class="h-8 text-xs gap-1" @click="addFestivity">
        <Plus class="h-3.5 w-3.5" />
        Add
      </Button>
    </div>
  </div>
</template>
