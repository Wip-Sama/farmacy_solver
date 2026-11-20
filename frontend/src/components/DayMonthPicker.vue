<script setup lang="ts">
import { ref, watch } from 'vue'
import { Calendar as CalendarIcon, X } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Calendar } from '@/components/ui/calendar'
import { parseDate } from '@internationalized/date'

const props = withDefaults(
  defineProps<{
    modelValue?: string
    placeholder?: string
    year?: number
    class?: any
  }>(),
  {
    modelValue: '',
    placeholder: 'gg/mm',
    year: new Date().getFullYear(),
    class: '',
  }
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const isOpen = ref(false)
const calendarValue = ref<any>(undefined)

// Parse DD/MM string (e.g. "25/12") to CalendarDate for the active year
function parseDayMonth(str: string, activeYear: number): any {
  if (!str) return undefined
  try {
    const parts = str.split(/[\/\-.]/)
    if (parts.length >= 2) {
      const day = parseInt(parts[0], 10)
      const month = parseInt(parts[1], 10)
      const year = parts.length === 3 ? parseInt(parts[2], 10) : activeYear
      if (day > 0 && day <= 31 && month > 0 && month <= 12) {
        const paddedDay = day.toString().padStart(2, '0')
        const paddedMonth = month.toString().padStart(2, '0')
        return parseDate(`${year}-${paddedMonth}-${paddedDay}`)
      }
    }
  } catch {
    // ignore invalid dates
  }
  return undefined
}

function formatDayMonth(date: any): string {
  if (!date) return ''
  const day = date.day.toString().padStart(2, '0')
  const month = date.month.toString().padStart(2, '0')
  return `${day}/${month}`
}

watch(
  [() => props.modelValue, () => props.year],
  ([val, yr]) => {
    calendarValue.value = parseDayMonth(val, yr)
  },
  { immediate: true }
)

function handleDateSelect(val: any) {
  if (val) {
    emit('update:modelValue', formatDayMonth(val))
    isOpen.value = false
  }
}

function handleClear(e: Event) {
  e.stopPropagation()
  emit('update:modelValue', '')
  calendarValue.value = undefined
}
</script>

<template>
  <Popover v-model:open="isOpen">
    <PopoverTrigger as-child>
      <Button
        variant="outline"
        size="sm"
        :class="[
          'justify-between text-left font-mono text-xs h-8 px-2.5 border-border/40 hover:bg-accent/50',
          !modelValue ? 'text-muted-foreground' : 'text-foreground font-semibold',
          props.class,
        ]"
      >
        <span>{{ modelValue || placeholder }}</span>
        <div class="flex items-center gap-1 ml-2 shrink-0">
          <span
            v-if="modelValue"
            class="hover:text-destructive p-0.5 rounded cursor-pointer"
            @click="handleClear"
          >
            <X class="h-3 w-3 text-muted-foreground hover:text-destructive" />
          </span>
          <CalendarIcon class="h-3.5 w-3.5 opacity-75" />
        </div>
      </Button>
    </PopoverTrigger>
    <PopoverContent class="w-auto p-0 border-border/40 bg-card" align="start">
      <Calendar
        :model-value="calendarValue"
        @update:model-value="handleDateSelect"
        initial-focus
      />
    </PopoverContent>
  </Popover>
</template>
