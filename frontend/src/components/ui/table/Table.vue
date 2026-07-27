<script setup lang="ts">
import type { HTMLAttributes } from "vue"
import { cn } from "@/lib/utils"

const props = defineProps<{
  class?: HTMLAttributes["class"]
  noWrapper?: boolean
  divClass?: HTMLAttributes["class"]
}>()
</script>

<template>
  <template v-if="props.noWrapper">
    <table :class="cn('w-full caption-bottom text-sm', props.class)">
      <slot />
    </table>
  </template>
  <div v-else :class="cn('relative w-full overflow-auto', props.divClass)">
    <table :class="cn('w-full caption-bottom text-sm', props.class)">
      <slot />
    </table>
  </div>
</template>
