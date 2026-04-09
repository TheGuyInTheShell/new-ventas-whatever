<script setup lang="ts">
import { h, resolveComponent } from 'vue'
import { useFiatStore } from '~/stores/useFiatStore'
import { useMenuQuery, type MenuItem } from '~/composables/useMenuQuery'
import MenuFormModal from '~/components/menu/MenuFormModal.vue'
import MenuToolbar from '~/components/menu/MenuToolbar.vue'
import type { TableColumn } from '@nuxt/ui'


const fiatStore = useFiatStore()

// ── Data from composable ──
const {
  items,
  ingredientOptions,
  isLoading,
  saveMutation,
  deleteMutation,
} = useMenuQuery()

// ── Filter and Sort state ──
const searchQuery = ref('')
const sortBy = ref('name_asc')

const filteredItems = computed(() => {
  let result = [...items.value]

  // Filter
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter((item: MenuItem) => item.name.toLowerCase().includes(q))
  }

  // Sort
  result.sort((a: MenuItem, b: MenuItem) => {
    if (sortBy.value === 'name_asc') {
      return (a.name || '').localeCompare(b.name || '')
    } else if (sortBy.value === 'price_asc') {
      return (a.price || 0) - (b.price || 0)
    } else if (sortBy.value === 'price_desc') {
      return (b.price || 0) - (a.price || 0)
    }
    return 0
  })

  return result
})

// ── Form state ──
const isModalOpen = ref(false)
const editingItem = ref<any>(null)

// ── Ingredients detail modal ──
const isIngredientsModalOpen = ref(false)
const ingredientsModalData = ref<{ name: string; ingredients: any[] }>({ name: '', ingredients: [] })

function openIngredientsModal(row: any) {
  ingredientsModalData.value = {
    name: row.name,
    ingredients: row.ingredients || []
  }
  isIngredientsModalOpen.value = true
}

function getIngredientDetail(ing: any) {
  const id = typeof ing === 'number' ? ing : ing.id
  const opt = ingredientOptions.value.find((o: any) => o.value === id)
  return {
    name: opt?.label || `#${id}`,
    qty: (typeof ing === 'object' && ing.qty) ? ing.qty : 1,
    expression: (typeof ing === 'object' && ing.expression) ? ing.expression : (opt?.expression || 'unit'),
    price: opt?.price || 0
  }
}

// ── Resolve components for render functions ──
const UButton = resolveComponent('UButton')
const UIcon = resolveComponent('UIcon')

// ── Table columns (using cell render functions like inventory.vue) ──
const columns: TableColumn<MenuItem>[] = [
  {
    accessorKey: 'image',
    header: 'Image',
    cell: ({ row }) => {
      const imageId = row.original.image_id
      if (imageId) {
        return h('div', { class: 'dish-img rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700' }, [
          h('img', { src: imageId, class: 'w-full h-full object-cover', alt: 'Dish' })
        ])
      }
      return h('div', { class: 'w-12 h-12 rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 flex items-center justify-center text-gray-400' }, [
        h(UIcon, { name: 'i-lucide-image', class: 'w-5 h-5' })
      ])
    }
  },
  { accessorKey: 'name', header: 'Dish Name' },
  { accessorKey: 'prep_time', header: 'Prep Time' },
  {
    accessorKey: 'ingredients',
    header: 'Ingredients',
    cell: ({ row }) => {
      const ings = row.original.ingredients || []
      if (ings.length > 0) {
        return h(UButton, {
          variant: 'soft',
          color: 'neutral',
          size: 'xs',
          icon: 'i-lucide-list',
          label: `${ings.length} ingredients`,
          onClick: () => openIngredientsModal(row.original)
        })
      }
      return h('span', { class: 'text-gray-400 text-sm' }, '—')
    }
  },
  {
    accessorKey: 'price',
    header: 'Price',
    cell: ({ row }) => {
      const price = row.original.price
      if (!price) return h('span', { class: 'text-gray-400' }, '-')
      const fiat = fiatStore.fiats.find((f) => f.id === row.original.currency_id)
      const expr = fiat?.expression || row.original.currency || ''
      return h('span', {}, `${price} ${expr}`)
    }
  },
  {
    id: 'actions',
    header: 'Actions',
    cell: ({ row }) => {
      return h('div', { class: 'flex items-center gap-1' }, [
        h(UButton, {
          icon: 'i-lucide-edit',
          variant: 'ghost',
          color: 'neutral',
          size: 'xs',
          onClick: () => editItem(row.original)
        }),
        h(UButton, {
          icon: 'i-lucide-trash',
          variant: 'ghost',
          color: 'error',
          size: 'xs',
          onClick: () => confirmDelete(row.original)
        })
      ])
    }
  }
]

// ── Lifecycle ──
onMounted(async () => {
  await fiatStore.fetchFiats()
})

// ── Helpers ──
function openAddModal() {
  editingItem.value = null
  isModalOpen.value = true
}

function editItem(item: any) {
  editingItem.value = item
  isModalOpen.value = true
}

async function handleItemSaved(payload: any) {
  await saveMutation.mutateAsync({
    editingItem: editingItem.value,
    formData: payload
  })
  isModalOpen.value = false
}

// ── Delete ──
const isDeleteConfirmOpen = ref(false)
const itemToDelete = ref<any>(null)

function confirmDelete(item: any) {
  itemToDelete.value = item
  isDeleteConfirmOpen.value = true
}

async function handleDelete() {
  if (itemToDelete.value) {
    await deleteMutation.mutateAsync(itemToDelete.value.id)
  }
  isDeleteConfirmOpen.value = false
  itemToDelete.value = null
}
</script>

<template>
  <div class="p-4 space-y-4 w-full">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold">Menu</h1>
      <UButton label="Add Dish" icon="i-lucide-plus" @click="openAddModal" color="primary" />
    </div>

    <MenuToolbar v-model:search="searchQuery" v-model:sortBy="sortBy" />

    <UTable :data="filteredItems" :columns="columns" :loading="isLoading" />

    <!-- Menu Form Modal -->
    <MenuFormModal
      v-model:open="isModalOpen"
      :editing-item="editingItem"
      :ingredient-options="ingredientOptions"
      @saved="handleItemSaved"
    />

    <!-- Ingredients Detail Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="isIngredientsModalOpen"
          class="fixed inset-0 z-50 flex items-center justify-center p-4"
          @click.self="isIngredientsModalOpen = false"
        >
          <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" />
          <div class="relative w-full max-w-md bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden" @click.stop>
            <!-- Header -->
            <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <div class="flex items-center gap-3">
                <div class="flex items-center justify-center w-9 h-9 rounded-lg bg-primary/10">
                  <UIcon name="i-lucide-list" class="w-4 h-4 text-primary" />
                </div>
                <div>
                  <h3 class="text-base font-semibold">{{ ingredientsModalData.name }}</h3>
                  <p class="text-xs text-gray-500">Ingredients breakdown</p>
                </div>
              </div>
              <UButton icon="i-lucide-x" variant="ghost" color="neutral" size="sm" @click="isIngredientsModalOpen = false" />
            </div>
            <!-- Body -->
            <div class="p-6 space-y-2 max-h-[60vh] overflow-y-auto">
              <div
                v-for="(ing, idx) in ingredientsModalData.ingredients"
                :key="idx"
                class="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-800"
              >
                <div class="flex-1">
                  <span class="font-medium text-sm">{{ getIngredientDetail(ing).name }}</span>
                  <span class="ml-2 text-xs text-gray-500">
                    {{ getIngredientDetail(ing).qty }} {{ getIngredientDetail(ing).expression }}
                  </span>
                </div>
                <span class="font-mono text-sm text-primary-600 dark:text-primary-400">
                  ${{ (getIngredientDetail(ing).price * getIngredientDetail(ing).qty).toFixed(2) }}
                </span>
              </div>
              <!-- Total row -->
              <div class="flex items-center justify-between pt-3 mt-2 border-t border-gray-200 dark:border-gray-700">
                <span class="text-sm font-semibold">Total</span>
                <span class="font-mono text-sm font-bold text-primary-600 dark:text-primary-400">
                  ${{ ingredientsModalData.ingredients.reduce((sum: number, ing: any) => {
                    const d = getIngredientDetail(ing)
                    return sum + d.price * d.qty
                  }, 0).toFixed(2) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Delete Confirmation Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="isDeleteConfirmOpen"
          class="fixed inset-0 z-50 flex items-center justify-center p-4"
          @click.self="isDeleteConfirmOpen = false"
        >
          <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" />
          <div class="relative w-full max-w-sm bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden" @click.stop>
            <div class="p-6 text-center space-y-4">
              <div class="flex items-center justify-center w-12 h-12 mx-auto rounded-full bg-red-100 dark:bg-red-900/30">
                <UIcon name="i-lucide-trash" class="w-6 h-6 text-red-600 dark:text-red-400" />
              </div>
              <div>
                <h3 class="text-lg font-semibold">Delete Dish</h3>
                <p class="text-sm text-gray-500 mt-1">
                  Are you sure you want to delete <strong>{{ itemToDelete?.name }}</strong>? This action cannot be undone.
                </p>
              </div>
              <div class="flex gap-3 justify-center">
                <UButton label="Cancel" variant="outline" color="neutral" @click="isDeleteConfirmOpen = false" />
                <UButton label="Delete" color="error" icon="i-lucide-trash" :loading="deleteMutation.isPending.value" @click="handleDelete" />
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

</style>

<style>

.dish-img {
  width: 100%;
  height: 100%;
  max-width: 320px;
  max-height: 320px;
  aspect-ratio: 1;
}

tr:first-child td {
  max-width: 120px;
  width: fit-content;
}
</style>
