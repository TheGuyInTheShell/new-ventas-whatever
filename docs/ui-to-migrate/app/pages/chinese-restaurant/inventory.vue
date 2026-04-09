<script setup lang="ts">
import { useFiatStore } from '~/stores/useFiatStore'
import { useInventoryQuery, type InventoryItem } from '~/composables/useInventoryQuery'
import InventoryFormModal from '~/components/inventory/InventoryFormModal.vue'
import { h, resolveComponent } from 'vue'
import type { TableColumn } from '@nuxt/ui'
import AdjustStockModal from '~/components/inventory/AdjustStockModal.vue'

type InventoryType = 'ingredient' | 'utensil' | 'consumable' | 'other'
type InventoryTypeSelector = 'all' | InventoryType

const fiatStore = useFiatStore()

// Filter & pagination state
const page = ref(1)
const typeFilter = ref<InventoryTypeSelector>('all')
const nameQuery = ref('')
const sortOrder = ref<'asc' | 'desc'>('asc')

const typeOptions = [
  { label: 'All types', value: 'all' },
  { label: 'Ingredient', value: 'ingredient' },
  { label: 'Utensil', value: 'utensil' },
  { label: 'Consumable', value: 'consumable' },
  { label: 'Other', value: 'other' }
]

// Reset page when filters change
watch([typeFilter, sortOrder, nameQuery], () => {
  page.value = 1
})

// TanStack Query
const {
  items,
  pagination,
  isLoading,
  isError,
  error,
  saveMutation,
  deleteMutation,
  refetch
} = useInventoryQuery({ page, type: typeFilter, ord: sortOrder, name: nameQuery })

// Columns
const UBadge = resolveComponent('UBadge')
const UButton = resolveComponent('UButton')

const typeColor: Record<InventoryType, string> = {
  ingredient: 'primary',
  utensil: 'neutral',
  consumable: 'success',
  other: 'warning'
}

type TFormatDataUi = 'size'
const formatDataUi: Record<TFormatDataUi, string> = {
  size: 'xl'
}

const columns: TableColumn<InventoryItem>[] = [
  {
    accessorKey: 'name',
    header: 'Name',
    cell: ({ row }) => {
      return h('span', { class: 'text-lg font-medium text-gray-900 dark:text-white' }, row.original.name)
    }
  },
  {
    accessorKey: 'balance',
    header: 'Stock',
    cell: ({ row }) => {
      return h('div', { class: 'flex items-center gap-1' }, [
        h('span', { class: 'text-lg font-medium text-gray-900 dark:text-white' }, row.original.balance ?? 0),
        h('span', { class: 'text-lg text-gray-500' }, row.original.expression)
      ])
    }
  },
  {
    accessorKey: 'type',
    header: 'Type',
    cell: ({ row }) => {
      const type = row.original.type as InventoryType
      return h(UBadge, {
        label: type,
        variant: 'subtle',
        size: formatDataUi.size,
        color: typeColor?.[type] ?? 'neutral'
      })
    }
  },
  {
    accessorKey: 'expression',
    header: 'Unit Rate',
    cell: ({ row }) => {
      return h('div', { class: 'flex items-center gap-1' }, [
        h('span', { class: 'text-lg font-medium text-gray-900 dark:text-white' }, row.original.price ? 1 : 0), // Assuming price implies 1 unit
        h('span', { class: 'text-lg text-gray-500' }, row.original.expression)
      ])
    }
  },
  {
    accessorKey: 'price',
    header: 'Price',
    cell: ({ row }) => {
      const price = row.original.price
      const currency = row.original.currency
      if (!price) return h('span', { class: 'text-gray-400' }, '-')

      return h('div', { class: 'flex items-center gap-1' }, [
        h('span', { class: 'text-lg font-medium text-gray-900 dark:text-white' }, price),
        h('span', { class: 'text-lg text-gray-500' }, currency)
      ])
    }
  },
  {
    id: 'actions',
    header: '',
    cell: ({ row }) => {
      return h('div', { class: 'flex justify-end gap-1 w-full' }, [
        h(UButton, {
          icon: 'i-lucide-arrow-right-left',
          variant: 'ghost',
          color: 'primary',
          size: formatDataUi.size,
          onClick: () => openAdjustModal(row.original)
        }),
        h(UButton, {
          icon: 'i-lucide-edit',
          variant: 'ghost',
          color: 'neutral',
          size: formatDataUi.size,
          onClick: () => editItem(row.original)
        }),
        h(UButton, {
          icon: 'i-lucide-trash-2',
          variant: 'ghost',
          color: 'error',
          size: formatDataUi.size,
          onClick: () => openDeleteModal(row.original)
        })
      ])
    }
  }
]

onMounted(async () => {
  await fiatStore.fetchFiats()
})

// Form Logic
const isModalOpen = ref(false)
const editingItem = ref<InventoryItem | null>(null)

function openAddModal() {
  editingItem.value = null
  isModalOpen.value = true
}

function editItem(item: InventoryItem) {
  editingItem.value = item
  isModalOpen.value = true
}

// Adjust Stock Logic
const adjustModalOpen = ref(false)
const adjustItem = ref<InventoryItem | null>(null)

function openAdjustModal(item: InventoryItem) {
  adjustItem.value = item
  adjustModalOpen.value = true
}

// Delete Logic
const deleteModalOpen = ref(false)
const itemToDelete = ref<InventoryItem | null>(null)

function openDeleteModal(item: InventoryItem) {
  itemToDelete.value = item
  deleteModalOpen.value = true
}

async function confirmDelete() {
  if (!itemToDelete.value) return
  await deleteMutation.mutateAsync({
    id: itemToDelete.value.id,
    comparisonId: itemToDelete.value.comparison_id
  })
  deleteModalOpen.value = false
}

// Pagination helpers
function goToPage(p: number) {
  page.value = p
}
</script>

<template>
  <div class="p-4 space-y-4 w-full relative min-h-screen pb-24">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold">
        Inventory
      </h1>
      <UButton
        label="Add Item"
        icon="i-lucide-plus"
        color="primary"
        class="hidden sm:flex"
        @click="openAddModal"
      />
    </div>

    <!-- Filters Bar -->
    <div class="flex flex-wrap items-center gap-3">
      <UInput
        v-model="nameQuery"
        placeholder="Search by name..."
        icon="i-lucide-search"
        class="w-64"
      />
      <USelect
        v-model="typeFilter"
        :items="typeOptions"
        placeholder="Filter by type"
        class="w-40"
      />
      <UButton
        :icon="sortOrder === 'asc' ? 'i-lucide-arrow-up-narrow-wide' : 'i-lucide-arrow-down-wide-narrow'"
        :label="sortOrder === 'asc' ? 'A → Z' : 'Z → A'"
        variant="outline"
        color="neutral"
        @click="sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'"
      />
      <span class="ml-auto text-lg text-gray-500 dark:text-gray-400">
        {{ pagination.total }} item{{ pagination.total !== 1 ? 's' : '' }}
      </span>
    </div>

    <!-- Error State -->
    <div v-if="isError" class="p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 text-sm flex items-center gap-2">
      <UIcon name="i-lucide-alert-circle" class="w-5 h-5 shrink-0" />
      <span>Failed to load inventory. {{ (error as Error)?.message }}</span>
    </div>

    <!-- Main Table Card -->
    <UCard :ui="{ body: 'p-0' }">
      <!-- Loading Overlay -->
      <div v-if="isLoading && items.length === 0" class="absolute inset-0 z-50 flex items-center justify-center bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm rounded-xl">
        <div class="flex flex-col items-center gap-3">
          <UIcon name="i-lucide-loader-2" class="w-10 h-10 animate-spin text-primary" />
          <span class="text-sm font-medium">Fetching inventory...</span>
        </div>
      </div>

      <UTable
        v-else
        :columns="columns"
        :data="items"
        :loading="isLoading"
        :empty-state="{ icon: 'i-lucide-package-x', text: 'No inventory items found. Add some above.' }"
        class="w-full"
      />

      <div class="px-6 py-4 flex items-center justify-between border-t border-gray-200 dark:border-gray-800">
        <span class="text-sm text-gray-500">
          Showing <span class="font-medium text-gray-900 dark:text-white">{{ items.length }}</span> items
        </span>

        <UPagination
          v-model="page"
          :page-count="pagination.page_size"
          :total="pagination.total"
        />
      </div>
    </UCard>

    <!-- Floating Action Button -->
    <div class="fixed bottom-8 right-8 z-40">
      <UButton
        icon="i-lucide-plus"
        size="xl"
        color="primary"
        class="rounded-full h-14 w-14 shadow-lg flex items-center justify-center"
        @click="openAddModal"
      />
    </div>

    <!-- Modals -->
    <InventoryFormModal
      v-model:open="isModalOpen"
      :editing-item="editingItem"
      :save-mutation="saveMutation"
      @saved="refetch"
    />

    <AdjustStockModal
      v-model:open="adjustModalOpen"
      :item="adjustItem"
      @adjusted="refetch"
    />

    <UModal v-model:open="deleteModalOpen" title="Delete Item" description="Are you sure you want to delete this item? This action cannot be undone.">
      <template #footer>
        <div class="flex justify-end gap-2 px-4 pb-4">
          <UButton
            label="Cancel"
            color="neutral"
            variant="ghost"
            @click="deleteModalOpen = false"
          />
          <UButton
            label="Delete"
            color="error"
            :loading="deleteMutation.isPending.value"
            @click="confirmDelete"
          />
        </div>
      </template>
    </UModal>
  </div>
</template>
