import { defineStore } from 'pinia'
import { useFiatStore } from './useFiatStore'

export const useInventoryStore = defineStore('inventory', () => {
  const items = ref<any[]>([])
  const loading = ref(false)
  const fiatStore = useFiatStore()
  const config = useRuntimeConfig()
  const toast = useToast()

  async function fetchItems() {
    loading.value = true
    try {
      const { data }: any = await $fetch(`${config.public.apiBase}/values/`, {
        query: { context: 'chinese_restaurant' }
      })

      const rawItems = data || []

      const { data: comparisons }: any = await $fetch(`${config.public.apiBase}/comparison_values/`, {
        query: { context: 'chinese_restaurant' }
      })

      if (comparisons) {
        items.value = rawItems.map((item: any) => {
          const comp = comparisons.find((c: any) => c.source_value?.id === item.id)
          if (comp) {
            return {
              ...item,
              price: comp.quantity_to,
              currency: comp.target_value?.expression,
              currency_id: comp.target_value?.id,
              comparison_id: comp.id
            }
          }
          return item
        })
      } else {
        items.value = rawItems
      }
    } catch (error) {
      console.error('Error fetching inventory', error)
      toast.add({ title: 'Error', description: 'Failed to fetch inventory', color: 'error' })
    } finally {
      loading.value = false
    }
  }

  async function saveItem(editingItem: any, formData: any) {
    try {
      let item: any
      if (editingItem) {
        // Update
        item = await $fetch(`${config.public.apiBase}/values/id/${editingItem.id}`, {
          method: 'PUT',
          body: {
            name: formData.name,
            type: formData.type,
            expression: formData.expression,
            context: 'chinese_restaurant'
          }
        })

        // Handle Comparison
        if (editingItem.comparison_id) {
          await $fetch(`${config.public.apiBase}/comparison_values/id/${editingItem.comparison_id}`, {
            method: 'PUT',
            body: {
              quantity_from: 1,
              quantity_to: formData.price,
              value_from: editingItem.id,
              value_to: formData.currency_id,
              context: 'chinese_restaurant'
            }
          })
        } else if (formData.price > 0) {
          await $fetch(`${config.public.apiBase}/comparison_values/`, {
            method: 'POST',
            body: {
              quantity_from: 1,
              quantity_to: formData.price,
              value_from: editingItem.id,
              value_to: formData.currency_id,
              context: 'chinese_restaurant'
            }
          })
        }
      } else {
        // Create
        item = await $fetch(`${config.public.apiBase}/values/`, {
          method: 'POST',
          body: {
            name: formData.name,
            type: formData.type,
            expression: formData.expression,
            context: 'chinese_restaurant'
          }
        })

        if (formData.price > 0) {
          await $fetch(`${config.public.apiBase}/comparison_values/`, {
            method: 'POST',
            body: {
              quantity_from: 1,
              quantity_to: formData.price,
              value_from: item.id,
              value_to: formData.currency_id,
              context: 'chinese_restaurant'
            }
          })
        }
      }

      await fetchItems()
      return true
    } catch (error) {
      console.error('Error saving item', error)
      toast.add({ title: 'Error', description: 'Failed to save item', color: 'error' })
      return false
    }
  }

  async function deleteItem(id: number, comparisonId?: number) {
    try {
      await $fetch(`${config.public.apiBase}/values/id/${id}`, {
        method: 'DELETE'
      })
      if (comparisonId) {
        await $fetch(`${config.public.apiBase}/comparison_values/id/${comparisonId}`, {
          method: 'DELETE'
        })
      }
      await fetchItems()
      return true
    } catch (error) {
      console.error('Error deleting item', error)
      toast.add({ title: 'Error', description: 'Failed to delete item', color: 'error' })
      return false
    }
  }

  return {
    items,
    loading,
    fetchItems,
    saveItem,
    deleteItem
  }
})
