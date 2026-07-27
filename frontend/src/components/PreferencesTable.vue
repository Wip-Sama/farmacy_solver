<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAppStore } from '@/stores/appStore'
import type { PharmacyPreference } from '@/stores/appStore'
import { Button } from '@/components/ui/button'
import DayMonthPicker from '@/components/DayMonthPicker.vue'
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
import { Plus, Trash2 } from 'lucide-vue-next'

const props = defineProps<{
  items?: PharmacyPreference[]
}>()

const emit = defineEmits<{
  (e: 'update:items', val: PharmacyPreference[]): void
}>()

const store = useAppStore()

const list = computed<PharmacyPreference[]>(() => {
  return props.items !== undefined ? props.items : store.settings.pharmacy_preferences
})

const newPharmacyId = ref('1')
const newDate = ref('')
const newState = ref('Closed')

const preferenceStateOptions = [
  'Closed',
  'Open',
  'Preferably Closed',
  'Preferably Open'
]

function getPharmacyLabel(p: { id: number; name?: string }): string {
  if (p && p.name && p.name.trim() !== '') {
    return p.name
  }
  return `F${p.id}`
}

function updateList(newList: PharmacyPreference[]) {
  if (props.items !== undefined) {
    emit('update:items', newList)
  } else {
    store.updateSettings({ pharmacy_preferences: newList })
  }
}

function addPreference() {
  if (!newDate.value) return
  const updated = [
    ...list.value,
    { pharmacy_id: parseInt(newPharmacyId.value, 10), date: newDate.value, state: newState.value }
  ]
  updateList(updated)
  newDate.value = ''
}

function updatePreference(index: number, field: 'pharmacy_id' | 'date' | 'state', value: any) {
  const updated = [...list.value]
  if (field === 'pharmacy_id') {
    updated[index] = { ...updated[index], pharmacy_id: parseInt(value, 10) || 1 }
  } else if (field === 'date') {
    updated[index] = { ...updated[index], date: value }
  } else if (field === 'state') {
    updated[index] = { ...updated[index], state: value }
  }
  updateList(updated)
}

function removePreference(index: number) {
  const updated = list.value.filter((_: unknown, i: number) => i !== index)
  updateList(updated)
}
</script>

<template>
  <div class="space-y-3">
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-semibold text-foreground">Preferences</h3>
    </div>

    <!-- Explanation note from wireframe -->
    <p class="text-xs text-muted-foreground italic leading-relaxed">
      Imposta preferenze specifiche di apertura/chiusura per ogni farmacia.
    </p>

    <!-- Table -->
    <div class="rounded-md border border-border/40 overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow class="hover:bg-transparent border-b border-border/40">
            <TableHead class="w-36 font-semibold text-muted-foreground">Pharmacy</TableHead>
            <TableHead class="font-semibold text-muted-foreground">Date (gg/mm)</TableHead>
            <TableHead class="w-44 font-semibold text-muted-foreground">State</TableHead>
            <TableHead class="text-right w-16 font-semibold text-muted-foreground">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow v-for="(pref, index) in list" :key="index" class="border-b border-border/40">
            <TableCell class="p-1.5">
              <Select 
                :model-value="pref.pharmacy_id.toString()" 
                @update:model-value="(val: any) => updatePreference(index, 'pharmacy_id', val)"
              >
                <SelectTrigger class="h-8 text-xs font-bold text-primary w-32 border-border/40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem 
                    v-for="p in (store.settings.pharmacies.length > 0 ? store.settings.pharmacies : [{ id: 1 }, { id: 2 }, { id: 3 }])" 
                    :key="p.id" 
                    :value="p.id.toString()"
                  >
                    {{ getPharmacyLabel(p) }}
                  </SelectItem>
                </SelectContent>
              </Select>
            </TableCell>
            <TableCell class="p-1.5">
              <DayMonthPicker 
                :model-value="pref.date" 
                @update:model-value="(val: string) => updatePreference(index, 'date', val)"
                class="w-36"
              />
            </TableCell>
            <TableCell class="p-1.5">
              <Select 
                :model-value="pref.state" 
                @update:model-value="(val: any) => updatePreference(index, 'state', val)"
              >
                <SelectTrigger class="h-8 text-xs w-40 font-medium text-amber-500 border-border/40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="opt in preferenceStateOptions" :key="opt" :value="opt">
                    {{ opt }}
                  </SelectItem>
                </SelectContent>
              </Select>
            </TableCell>
            <TableCell class="text-right p-1.5">
              <Button 
                variant="ghost" 
                size="icon" 
                class="h-7 w-7 text-destructive hover:text-destructive hover:bg-destructive/10"
                @click="removePreference(index)"
              >
                <Trash2 class="h-3.5 w-3.5" />
              </Button>
            </TableCell>
          </TableRow>
          <TableRow v-if="list.length === 0">
            <TableCell colspan="4" class="text-center text-xs text-muted-foreground italic py-4">
              No pharmacy preferences added.
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </div>

    <!-- Add Row Form -->
    <div class="flex items-center gap-2 pt-1">
      <Select v-model="newPharmacyId">
        <SelectTrigger class="h-8 text-xs w-32 border-border/40">
          <SelectValue placeholder="Pharmacy" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem 
            v-for="p in (store.settings.pharmacies.length > 0 ? store.settings.pharmacies : [{ id: 1 }, { id: 2 }, { id: 3 }])" 
            :key="p.id" 
            :value="p.id.toString()"
          >
            {{ getPharmacyLabel(p) }}
          </SelectItem>
        </SelectContent>
      </Select>

      <DayMonthPicker 
        v-model="newDate" 
        placeholder="gg/mm"
        class="w-36"
      />

      <Select v-model="newState">
        <SelectTrigger class="h-8 text-xs w-40 border-border/40">
          <SelectValue placeholder="State" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem v-for="opt in preferenceStateOptions" :key="opt" :value="opt">
            {{ opt }}
          </SelectItem>
        </SelectContent>
      </Select>

      <Button size="sm" variant="secondary" class="h-8 text-xs gap-1" @click="addPreference">
        <Plus class="h-3.5 w-3.5" />
        Add
      </Button>
    </div>
  </div>
</template>
