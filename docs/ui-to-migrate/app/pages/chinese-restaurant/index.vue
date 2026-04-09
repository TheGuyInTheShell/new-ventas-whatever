<script setup lang="ts">
import { VisXYContainer, VisLine, VisAxis, VisStackedBar, VisTooltip, VisCrosshair } from '@unovis/vue'
import { StackedBar } from '@unovis/ts'

// Mock Data
const salesData = [
  { x: 1, y: 100 },
  { x: 2, y: 150 },
  { x: 3, y: 120 },
  { x: 4, y: 200 },
  { x: 5, y: 180 }
]

const expensesData = [
  { x: 1, y: 80 },
  { x: 2, y: 100 },
  { x: 3, y: 90 },
  { x: 4, y: 150 },
  { x: 5, y: 120 }
]

const x = (d: any) => d.x
const y = (d: any) => d.y

const navigateToChat = () => {
  navigateTo('/chinese-restaurant/chat')
}
</script>

<template>
  <div class="p-4 space-y-4 w-full">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold">
        Dashboard
      </h1>
      <UButton
        icon="i-lucide-message-square"
        label="AI Assistant"
        color="primary"
        @click="navigateToChat"
      />
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <UCard>
        <template #header>
          <h3 class="font-semibold">
            Sales Overview
          </h3>
        </template>
        <div class="h-64">
          <VisXYContainer :data="salesData">
            <VisLine :x="x" :y="y" color="#10b981" />
            <VisAxis type="x" />
            <VisAxis type="y" />
            <VisTooltip />
            <VisCrosshair />
          </VisXYContainer>
        </div>
      </UCard>

      <UCard>
        <template #header>
          <h3 class="font-semibold">
            Expenses
          </h3>
        </template>
        <div class="h-64">
          <VisXYContainer :data="expensesData">
            <VisStackedBar :x="x" :y="y" color="#ef4444" />
            <VisAxis type="x" />
            <VisAxis type="y" />
            <VisTooltip />
          </VisXYContainer>
        </div>
      </UCard>
    </div>

    <!-- Placeholder for more widgets -->
    <UCard>
      <div class="text-center text-gray-500 py-8">
        More analytics coming soon...
      </div>
    </UCard>
  </div>
</template>
