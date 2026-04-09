<script setup lang="ts">
import { sub } from 'date-fns'
import type { DropdownMenuItem } from '@nuxt/ui'
import type { Period, Range } from '~/types'

const { isNotificationsSlideoverOpen } = useDashboard()
const permissionStore = usePermissionStore()
const toast = useToast()

const isDev = process.dev
const isSeeding = ref(false)

async function handleSeed() {
  isSeeding.value = true
  try {
    await permissionStore.seedPermissions()
    toast.add({
      title: 'Success',
      description: 'Permissions seeded successfully!',
      color: 'success'
    })
  } catch (error) {
    console.error('Seeding failed', error)
    toast.add({
      title: 'Error',
      description: 'Failed to seed permissions.',
      color: 'error'
    })
  } finally {
    isSeeding.value = false
  }
}

const items = [[{
  label: 'New mail',
  icon: 'i-lucide-send',
  to: '/inbox'
}, {
  label: 'New customer',
  icon: 'i-lucide-user-plus',
  to: '/customers'
}]] satisfies DropdownMenuItem[][]

const range = shallowRef<Range>({
  start: sub(new Date(), { days: 14 }),
  end: new Date()
})
const period = ref<Period>('daily')
</script>

<template>
  <UDashboardPanel id="home">
    <template #header>
      <UDashboardNavbar title="Home" :ui="{ right: 'gap-3' }">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>

        <template #right>
          <!-- Manual Seed Button (Dev only) -->
          <UButton
            v-if="isDev && permissionStore.roleName === 'owner'"
            icon="i-lucide-database-zap"
            :color="permissionStore.isPermissionBypassActive ? 'warning' : 'neutral'"
            variant="subtle"
            class="hidden lg:flex"
            :loading="isSeeding"
            @click="handleSeed"
          >
            {{ permissionStore.isPermissionBypassActive ? 'Seed Permissions' : 'Refresh Permissions' }}
          </UButton>

          <UTooltip text="Notifications" :shortcuts="['N']">
            <UButton
              color="neutral"
              variant="ghost"
              square
              @click="isNotificationsSlideoverOpen = true"
            >
              <UChip color="error" inset>
                <UIcon name="i-lucide-bell" class="size-5 shrink-0" />
              </UChip>
            </UButton>
          </UTooltip>

          <UDropdownMenu :items="items">
            <UButton icon="i-lucide-plus" size="md" class="rounded-full" />
          </UDropdownMenu>
        </template>
      </UDashboardNavbar>

      <UDashboardToolbar>
        <template #left>
          <!-- NOTE: The `-ms-1` class is used to align with the `DashboardSidebarCollapse` button here. -->
          <HomeDateRangePicker v-model="range" class="-ms-1" />

          <HomePeriodSelect v-model="period" :range="range" />
        </template>
      </UDashboardToolbar>
    </template>

    <template #body>
      <HomeStats :period="period" :range="range" />
      <HomeChart :period="period" :range="range" />
      <HomeSales :period="period" :range="range" />
    </template>
  </UDashboardPanel>
</template>
