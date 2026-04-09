import { defineStore } from 'pinia'

export const useFiatStore = defineStore('fiat', () => {
  const fiats = ref<any[]>([])
  const mainFiatId = ref<number | null>(null)
  const comparisons = ref<any[]>([])
  const loading = ref(false)
  const toast = useToast()
  const exchangeRates = ref<number[]>([])

  async function fetchExchangeRates() {
    await fetchFiats()

    // Populate main rates from comparisons
    if (comparisons.value) {
      comparisons.value.forEach((comp: any) => {
        console.log(comp)
        if (comp.context === 'main') {
          // 1 Main = X Other
          if (comp.value_from === mainFiatId.value) {
            exchangeRates.value[comp.value_to] = comp.quantity_to / comp.quantity_from
          } else if (comp.value_to === mainFiatId.value) {
            exchangeRates.value[comp.value_from] = comp.quantity_from / comp.quantity_to
          }
        }
      })
    }
  }

  // Fetch all global fiat values
  async function fetchFiats() {
    loading.value = true
    try {
      const config = useRuntimeConfig()
      const { data }: any = await $fetch(`${config.public.apiBase}/values/query`, {
        method: 'POST',
        body: {
          type: 'fiat',
          context: 'global',
          page_size: 100,
          balances: true
        }
      })
      fiats.value = data || []
      // Allow fetching comparisons for exchange rates
      const mainRes: any = await $fetch(`${config.public.apiBase}/comparison_values/`, {
        query: { context: 'main' }
      })

      const customRes: any = await $fetch(`${config.public.apiBase}/comparison_values/`, {
        query: { context: 'custom' }
      })

      const mainComps = mainRes?.data || []
      const customComps = customRes?.data || []
      comparisons.value = [...mainComps, ...customComps]

      await fetchMainFiat()
    } catch (error) {
      console.error('Failed to fetch fiats', error)
      toast.add({
        title: 'Error',
        description: 'Failed to fetch fiat currencies',
        color: 'primary'
      })
    } finally {
      loading.value = false
    }
  }

  async function fetchMainFiat() {
    try {
      const config = useRuntimeConfig()
      // We store the main fiat ID in options with context=global and name=main_fiat_currency
      const { data }: any = await $fetch(`${config.public.apiBase}/options/`, {
        query: {
          context: 'global'
        }
      })

      const mainOption = data.find((o: any) => o.name === 'main_fiat_currency')
      if (mainOption) {
        mainFiatId.value = parseInt(mainOption.value)
      }
    } catch (error) {
      console.error('Failed to fetch main fiat', error)
    }
  }

  async function setMainFiat(id: number) {
    try {
      const config = useRuntimeConfig()
      // Check if option exists, if so update, else create
      // For simplicity, we can try to find and then update/create
      // Or just create using a specific unique constraint handling if backend supports upsert
      // The backend controller seems to be basic CRUD.

      // First fetch to see if it exists (we already did in fetchMainFiat but let's be safe or use what we have)
      // Ideally backend should have an upsert endpoint or we manage it here.

      const { data }: any = await $fetch(`${config.public.apiBase}/options/`, {
        query: { context: 'global' }
      })
      const mainOption = data.find((o: any) => o.name === 'main_fiat_currency')

      if (mainOption) {
        await $fetch(`${config.public.apiBase}/options/id/${mainOption.id}`, {
          method: 'PUT',
          body: {
            name: 'main_fiat_currency',
            context: 'global',
            value: id.toString()
          }
        })
      } else {
        await $fetch(`${config.public.apiBase}/options/`, {
          method: 'POST',
          body: {
            name: 'main_fiat_currency',
            context: 'global',
            value: id.toString()
          }
        })
      }
      mainFiatId.value = id
      toast.add({ title: 'Success', description: 'Main currency updated' })
    } catch (error) {
      console.error('Failed to set main fiat', error)
      toast.add({ title: 'Error', description: 'Failed to update main currency', color: 'error' })
    }
  }

  async function createFiat(name: string, expression: string) {
    try {
      const config = useRuntimeConfig()
      await $fetch(`${config.public.apiBase}/values/`, {
        method: 'POST',
        body: {
          name: name,
          expression: expression, // Using expression field for symbol (e.g. $)
          type: 'fiat',
          context: 'global'
        }
      })
      await fetchFiats()
      toast.add({ title: 'Success', description: 'Currency created' })
    } catch (error) {
      console.error('Failed to create fiat', error)
      toast.add({ title: 'Error', description: 'Failed to create currency', color: 'error' })
    }
  }

  async function createLink(fromId: number, toId: number, rate: number, context: string = 'main') {
    try {
      const config = useRuntimeConfig()

      // Check if comparison already exists
      const existing = comparisons.value.find(
        (c: any) => c.value_from === fromId && c.value_to === toId && c.context === context
      )

      if (existing) {
        // Update existing comparison
        await $fetch(`${config.public.apiBase}/comparison_values/id/${existing.id}`, {
          method: 'PUT',
          body: {
            quantity_from: 1,
            quantity_to: rate,
            value_from: fromId,
            value_to: toId,
            context: context
          }
        })
        toast.add({ title: 'Success', description: 'Exchange rate updated' })
      } else {
        // Create new comparison
        await $fetch(`${config.public.apiBase}/comparison_values/`, {
          method: 'POST',
          body: {
            quantity_from: 1,
            quantity_to: rate,
            value_from: fromId,
            value_to: toId,
            context: context
          }
        })
        toast.add({ title: 'Success', description: 'Exchange rate set' })
      }
      await refreshComparisons()
    } catch (error) {
      console.error('Failed to link fiats', error)
      toast.add({ title: 'Error', description: 'Failed to set exchange rate', color: 'error' })
    }
  }

  async function updateComparison(compId: number, fromId: number, toId: number, rate: number, context: string = 'custom') {
    try {
      const config = useRuntimeConfig()
      await $fetch(`${config.public.apiBase}/comparison_values/id/${compId}`, {
        method: 'PUT',
        body: {
          quantity_from: 1,
          quantity_to: rate,
          value_from: fromId,
          value_to: toId,
          context: context
        }
      })
      await refreshComparisons()
      toast.add({ title: 'Success', description: 'Exchange rate updated' })
    } catch (error) {
      console.error('Failed to update comparison', error)
      toast.add({ title: 'Error', description: 'Failed to update exchange rate', color: 'error' })
    }
  }

  async function deleteComparison(id: number) {
    try {
      const config = useRuntimeConfig()
      await $fetch(`${config.public.apiBase}/comparison_values/id/${id}`, {
        method: 'DELETE'
      })
      await refreshComparisons()
      toast.add({ title: 'Success', description: 'Comparison deleted' })
    } catch (error) {
      console.error('Failed to delete comparison', error)
      toast.add({ title: 'Error', description: 'Failed to delete comparison', color: 'error' })
    }
  }

  async function refreshComparisons() {
    try {
      const config = useRuntimeConfig()
      const mainRes: any = await $fetch(`${config.public.apiBase}/comparison_values/`, {
        query: { context: 'main' }
      })
      const customRes: any = await $fetch(`${config.public.apiBase}/comparison_values/`, {
        query: { context: 'custom' }
      })
      const mainComps = mainRes?.data || []
      const customComps = customRes?.data || []
      comparisons.value = [...mainComps, ...customComps]
    } catch (error) {
      console.error('Failed to refresh comparisons', error)
    }
  }

  async function deleteFiat(id: number) {
    try {
      const config = useRuntimeConfig()
      await $fetch(`${config.public.apiBase}/values/id/${id}`, {
        method: 'DELETE'
      })
      await fetchFiats()
      toast.add({ title: 'Success', description: 'Currency deleted' })
    } catch (error) {
      console.error('Failed to delete fiat', error)
      toast.add({ title: 'Error', description: 'Failed to delete currency', color: 'error' })
    }
  }

  return {
    fiats,
    mainFiatId,
    loading,
    fetchFiats,
    setMainFiat,
    createFiat,
    createLink,
    updateComparison,
    deleteComparison,
    deleteFiat,
    comparisons,
    exchangeRates,
    fetchExchangeRates
  }
})
