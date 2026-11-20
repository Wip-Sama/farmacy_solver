<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAppStore } from '@/stores/appStore'
import type { Pharmacy } from '@/stores/appStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
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
  items?: Pharmacy[]
}>()

const emit = defineEmits<{
  (e: 'update:items', val: Pharmacy[]): void
}>()

const store = useAppStore()

const list = computed<Pharmacy[]>(() => {
  return props.items !== undefined ? props.items : store.settings.pharmacies
})

const newName = ref('')
const newLocation = ref('centro')

function updateList(newList: Pharmacy[]) {
  if (props.items !== undefined) {
    emit('update:items', newList)
  } else {
    store.updateSettings({ pharmacies: newList })
  }
}

function addPharmacy() {
  if (!newName.value.trim()) return
  const nextId = list.value.length > 0 ? Math.max(...list.value.map((p) => p.id)) + 1 : 1
  const updated = [
    ...list.value,
    { id: nextId, name: newName.value.trim(), location: newLocation.value },
  ]
  updateList(updated)
  newName.value = ''
}

function updatePharmacy(index: number, field: 'id' | 'name' | 'location', value: any) {
  const updated = [...list.value]
  if (field === 'id') {
    const parsed = parseInt(value, 10)
    updated[index] = { ...updated[index], id: isNaN(parsed) ? updated[index].id : parsed }
  } else if (field === 'name') {
    updated[index] = { ...updated[index], name: value }
  } else if (field === 'location') {
    updated[index] = { ...updated[index], location: value }
  }
  updateList(updated)
}

function removePharmacy(index: number) {
  const updated = list.value.filter((_, i) => i !== index)
  updateList(updated)
}
</script>

<template>
  <div class="space-y-3">
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-semibold text-foreground">Pharmacies</h3>
    </div>

    <div class="rounded-md border border-border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead class="w-16">ID</TableHead>
            <TableHead>Name</TableHead>
            <TableHead class="w-36">Location</TableHead>
            <TableHead class="text-right w-16">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow v-for="(pharm, index) in list" :key="pharm.id">
            <TableCell class="p-1.5 font-bold text-xs text-primary font-mono">
              <div class="flex items-center gap-1">
                <span>F</span>
                <Input
                  type="number"
                  :model-value="pharm.id"
                  @change="(e: Event) => updatePharmacy(index, 'id', (e.target as HTMLInputElement).value)"
                  class="h-7 text-xs w-12 font-mono p-1 text-center bg-transparent border-transparent hover:border-border focus:border-primary"
                />
              </div>
            </TableCell>
            <TableCell class="p-1.5">
              <Input
                :model-value="pharm.name"
                @change="(e: Event) => updatePharmacy(index, 'name', (e.target as HTMLInputElement).value)"
                placeholder="Pharmacy Name"
                class="h-7 text-xs bg-transparent border-transparent hover:border-border focus:border-primary"
              />
            </TableCell>
            <TableCell class="p-1.5">
              <Select
                :model-value="pharm.location"
                @update:model-value="(val: any) => updatePharmacy(index, 'location', String(val))"
              >
                <SelectTrigger class="h-7 text-xs w-28">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="centro">centro</SelectItem>
                  <SelectItem value="marina">marina</SelectItem>
                </SelectContent>
              </Select>
            </TableCell>
            <TableCell class="text-right p-1.5">
              <Button
                variant="ghost"
                size="icon"
                class="h-7 w-7 text-destructive hover:text-destructive hover:bg-destructive/10"
                @click="removePharmacy(index)"
              >
                <Trash2 class="h-3.5 w-3.5" />
              </Button>
            </TableCell>
          </TableRow>
          <TableRow v-if="list.length === 0">
            <TableCell colspan="4" class="text-center text-xs text-muted-foreground italic py-4">
              No pharmacies defined.
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </div>

    <div class="flex items-center gap-2 pt-1">
      <Input
        v-model="newName"
        placeholder="Pharmacy Name"
        class="h-8 text-xs flex-1"
        @keyup.enter="addPharmacy"
      />
      <Select v-model="newLocation">
        <SelectTrigger class="h-8 text-xs w-28">
          <SelectValue placeholder="Location" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="centro">centro</SelectItem>
          <SelectItem value="marina">marina</SelectItem>
        </SelectContent>
      </Select>
      <Button size="sm" variant="secondary" class="h-8 text-xs gap-1" @click="addPharmacy">
        <Plus class="h-3.5 w-3.5" />
        Add
      </Button>
    </div>
  </div>
</template>
