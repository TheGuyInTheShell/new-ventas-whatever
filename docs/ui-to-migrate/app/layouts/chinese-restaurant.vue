<script setup lang="ts">
const items = [
  {
    label: 'Dashboard',
    icon: 'i-lucide-layout-dashboard',
    to: '/chinese-restaurant'
  },
  {
    label: 'Inventory',
    icon: 'i-lucide-package',
    to: '/chinese-restaurant/inventory'
  },
  {
    label: 'Menu',
    icon: 'i-lucide-utensils-crossed',
    to: '/chinese-restaurant/menu'
  },
  {
    label: 'Sales',
    icon: 'i-lucide-shopping-cart',
    to: '/chinese-restaurant/sales'
  },
  {
    label: 'Settings',
    icon: 'i-lucide-settings',
    to: '/chinese-restaurant/settings'
  }
]
</script>

<template>
  <UDashboardLayout>
    <UDashboardSidebar>
      <template #header>
        <div class="flex items-center gap-2 px-4 py-2">
          <span class="font-bold text-lg">Chinese Restaurant</span>
        </div>
      </template>

      <UDashboardSidebarLinks :items="items" />
    </UDashboardSidebar>

    <UDashboardPage>
      <UDashboardNavbar title="Chinese Restaurant" :items="items" />

      <UDashboardPanel grow>
        <UDashboardPanelContent>
          <slot />
        </UDashboardPanelContent>
      </UDashboardPanel>
    </UDashboardPage>
  </UDashboardLayout>
</template>
