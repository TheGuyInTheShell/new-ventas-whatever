<script setup lang="ts">
import { VisXYContainer, VisLine, VisAxis, VisTooltip, VisCrosshair } from '@unovis/vue'
import type { Comparison } from '~/composables/useComparisons'

// Props
const props = defineProps<{
  comparisons: Comparison[]
}>()

// Transform comparisons to chart data
const chartData = computed(() => {
  return props.comparisons.map((c, index) => ({
    x: index,
    y: c.quantity_to / c.quantity_from,
    label: `${c.source_value?.expression || 'N/A'} → ${c.target_value?.expression || 'N/A'}`,
    from: c.source_value?.name || 'Unknown',
    to: c.target_value?.name || 'Unknown',
    rate: c.quantity_to / c.quantity_from
  }))
})

// Chart configuration
const x = (d: any) => d.x
const y = (d: any) => d.y

const template = (d: any) => `
  <div class="p-2 bg-white dark:bg-gray-800 rounded shadow-lg">
    <div class="font-semibold">${d.from} → ${d.to}</div>
    <div class="text-sm text-gray-500">Rate: ${d.rate.toFixed(4)}</div>
  </div>
`
</script>

<template>
  <div class="bg-white dark:bg-gray-900 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
    <h3 class="text-lg font-semibold mb-4">
      Value Comparison Rates
    </h3>

    <div v-if="comparisons.length === 0" class="text-center py-8 text-gray-500">
      No comparisons available. Create comparison relationships to visualize rates.
    </div>

    <div v-else class="h-64">
      <VisXYContainer :data="chartData">
        <VisLine
          :x="x"
          :y="y"
          color="#6366f1"
          :line-width="2"
        />
        <VisAxis type="x" :tick-format="(v: number) => `#${v + 1}`" />
        <VisAxis type="y" :tick-format="(v: number) => v.toFixed(2)" />
        <VisCrosshair color="#6366f1" />
        <VisTooltip :template="template" />
      </VisXYContainer>
    </div>

    <!-- Legend -->
    <div class="mt-4 flex flex-wrap gap-2">
      <div
        v-for="(c, i) in comparisons"
        :key="c.id"
        class="text-xs px-2 py-1 rounded-full bg-gray-100 dark:bg-gray-800"
      >
        <span class="font-medium">{{ c.source_value?.expression }}</span>
        →
        <span class="font-medium">{{ c.target_value?.expression }}</span>
        <span class="text-gray-500 ml-1">({{ (c.quantity_to / c.quantity_from).toFixed(2) }})</span>
      </div>
    </div>
  </div>
</template>
