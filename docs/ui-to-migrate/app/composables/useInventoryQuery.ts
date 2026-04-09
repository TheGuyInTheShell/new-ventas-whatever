import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import type { Ref } from 'vue'

// ==================== Types ====================

export interface InventoryItem {
  uid: string
  id: number
  name: string
  expression: string
  type: string
  context: string
  identifier?: string
  price?: number
  currency?: string
  currency_id?: number
  comparison_id?: number
  balance?: number
  balance_id?: number
  meta?: { uid: string, id: number, key: string, value: string | null }[]
}

export interface RSBalance {
  id: number
  quantity: number
  currency: string
  type: string
}

export interface RSComparisonValue {
  uid: string
  id: number
  quantity_from: number
  quantity_to: number
  value_from: number
  value_to: number
  context: string
  target_value?: {
    id: number
    expression: string
  }
}

export interface RSValue {
  uid: string
  id: number
  name: string
  expression: string
  type: string
  context: string
  identifier?: string
  meta?: { uid: string, id: number, key: string, value: string | null }[]
  comparison?: RSComparisonValue
  balances?: RSBalance[]
}

export interface RQValue {
  name: string
  expression: string
  type: string
  context: string
}

export interface RQComparisonValue {
  quantity_from: number
  quantity_to: number
  value_to: number | null
  context: string
}

export interface RQValueWithComparison {
  value: RQValue
  comparison_value: RQComparisonValue
  business_entity_ids: number[]
}

export interface InventoryFilters {
  page: Ref<number>
  type: Ref<string>
  ord: Ref<'asc' | 'desc'>
  name: Ref<string>
}

export interface PaginationMeta {
  total: number
  page: number
  page_size: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
  next_page: number | null
  prev_page: number | null
}

// ==================== Query Keys ====================

const INVENTORY_KEY = 'inventory-items'

// ==================== Composable ====================

export function useInventoryQuery(filters: InventoryFilters) {
  const config = useRuntimeConfig()
  const queryClient = useQueryClient()
  const toast = useToast()

  // ----- Query: fetch paginated inventory items -----
  const {
    data: queryData,
    isLoading,
    isError,
    error,
    refetch
  } = useQuery({
    queryKey: [INVENTORY_KEY, filters.page, filters.type, filters.ord, filters.name] as const,
    queryFn: async () => {
      // Build values query params
      const body: Record<string, string | number | boolean> = {
        page: filters.page.value,
        order: filters.ord.value,
        context: 'chinese_restaurant',
        meta: true,
        comparison: true, // Request comparison data (price)
        comparison_meta: true,
        balances: true, // Request stock balance data
        balance_type: 'Basic'
      }
      if (filters.type.value && filters.type.value !== 'all') {
        body.type = filters.type.value
      }
      if (filters.name.value) {
        body.name = filters.name.value
      }

      // Fetch paginated values with comparison data
      const response: InventoryQueryResponse = await $fetch(`${config.public.apiBase}/values/query`, {
        method: 'POST',
        body
      })

      const rawItems = response?.data || []
      const pagination: PaginationMeta = {
        total: response.total,
        page: response.page,
        page_size: response.page_size,
        total_pages: response.total_pages,
        has_next: response.has_next,
        has_prev: response.has_prev,
        next_page: response.next_page,
        prev_page: response.prev_page
      }

      interface InventoryQueryResponse extends PaginationMeta {
        data: RSValue[]
      }

      // Map response to InventoryItem
      const items: InventoryItem[] = rawItems.map((item: RSValue) => {
        const comp = item.comparison
        const baseItem: InventoryItem = {
          uid: item.uid,
          id: item.id,
          name: item.name,
          expression: item.expression,
          type: item.type,
          context: item.context,
          identifier: item.identifier,
          meta: item.meta,
          balance: item.balances?.[0]?.quantity || 0,
          balance_id: item.balances?.[0]?.id
        }

        if (comp) {
          return {
            ...baseItem,
            price: comp.quantity_to,
            currency: comp.target_value?.expression,
            currency_id: comp.target_value?.id,
            comparison_id: comp.id
          }
        }
        return baseItem
      })

      return { items, pagination }
    }
  })

  // Computed helpers
  const items = computed(() => queryData.value?.items ?? [])
  const pagination = computed(() => queryData.value?.pagination ?? {
    total: 0,
    page: 1,
    page_size: 10,
    total_pages: 1,
    has_next: false,
    has_prev: false,
    next_page: null,
    prev_page: null
  } as PaginationMeta)

  // ----- Mutation: save (create / update) -----
  const saveMutation = useMutation({
    mutationFn: async ({ editingItem, formData }: { editingItem: InventoryItem | null, formData: RQValueWithComparison }) => {
      // Ensure specific fields are capitalized
      if (formData.value) {
        formData.value.name = wellCapitalize(formData.value.name)
        formData.value.expression = wellCapitalize(formData.value.expression)
      }

      let item: RSValue
      if (editingItem) {
        // Update the value and its comparison via the 'd' module endpoint
        item = await $fetch(`${config.public.apiBase}/d/values_with_comparison/id/${editingItem.id}`, {
          method: 'PUT',
          body: formData
        })
      } else {
        // Create new value + comparison + balance via the 'd' module endpoint
        item = await $fetch(`${config.public.apiBase}/d/values_with_comparison/`, {
          method: 'POST',
          body: formData
        })
      }

      return item
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [INVENTORY_KEY] })
      toast.add({ title: 'Success', description: 'Item saved successfully' })
    },
    onError: (err) => {
      console.error('Error saving item', err)
      toast.add({ title: 'Error', description: 'Failed to save item', color: 'error' })
    }
  })

  // ----- Mutation: delete -----
  const deleteMutation = useMutation({
    mutationFn: async ({ id, comparisonId }: { id: number, comparisonId?: number }) => {
      await $fetch(`${config.public.apiBase}/values/id/${id}`, {
        method: 'DELETE'
      })
      if (comparisonId) {
        await $fetch(`${config.public.apiBase}/comparison_values/id/${comparisonId}`, {
          method: 'DELETE'
        })
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [INVENTORY_KEY] })
      toast.add({ title: 'Success', description: 'Item deleted' })
    },
    onError: (err) => {
      console.error('Error deleting item', err)
      toast.add({ title: 'Error', description: 'Failed to delete item', color: 'error' })
    }
  })

  return {
    // Query
    items,
    pagination,
    isLoading,
    isError,
    error,
    refetch,
    // Mutations
    saveMutation,
    deleteMutation
  }
}
