import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { useFiatStore } from '~/stores/useFiatStore'

// ==================== Types ====================

export interface MenuIngredient {
    id: number
    qty: number
    expression: string
}

export interface MenuItem {
    id: number
    uid: string
    name: string
    type: string
    context: string
    expression: string
    price: number
    currency: string
    currency_id?: number
    comparison_id?: number
    prep_time?: string
    image_id?: string
    ingredients?: MenuIngredient[]
    ref_super_values_ids?: number[]
    meta?: { uid: string; id: number; key: string; value: string | null }[]
}

export interface IngredientOption {
    label: string
    value: number
    expression: string
    price: number
}

export interface ValueRecord {
    id: number
    uid: string
    name: string
    type: string
    context: string
    expression: string
    identifier: string
    ref_super_values_ids?: number[]
    comparison?: {
        quantity_to: number
        target_value?: {
            expression: string
        }
    }
    meta?: { uid: string; id: number; key: string; value: string | null }[]
}

// ==================== Keys ====================

const MENU_KEY = 'menu-items'
const INGREDIENTS_KEY = 'menu-ingredients'

// ==================== Composable ====================

export function useMenuQuery() {
    const config = useRuntimeConfig()
    const queryClient = useQueryClient()
    const toast = useToast()

    const fiatStore = useFiatStore()

    // ----- Query: fetch menu items (dishes) -----
    const {
        data: menuData,
        isLoading: isMenuLoading,
        isError: isMenuError,
        error: menuError,
        refetch: refetchMenu
    } = useQuery({
        queryKey: [MENU_KEY, fiatStore.mainFiatId],
        queryFn: async () => {

            // 1. Fetch menu-type values conditionally joined with their fiat comparison
            const valuesRes = await $fetch<{ data?: ValueRecord[] }>(`${config.public.apiBase}/values/query`, {
                method: 'POST',
                body: {
                    context: 'chinese_restaurant',
                    type: 'menu',
                    page_size: 200,
                    meta: true,
                    comparison: true,
                    comparison_to_id: fiatStore.mainFiatId
                }
            })

            const rawItems = valuesRes?.data || []

            // 2. Map to MenuItem
            const items: MenuItem[] = rawItems.map((v: ValueRecord) => {
                // Parse meta fields
                const metaMap: Record<string, unknown> = {}
                v.meta?.forEach((m) => {
                    try {
                        if (['ingredients', 'price_decorators', 'meta_comparison_values'].includes(m.key)) {
                            metaMap[m.key] = m.value ? JSON.parse(m.value) : (() => { throw new Error('Invalid meta value') })()
                        } else {
                            metaMap[m.key] = m.value
                        }
                    } catch (e) {
                        console.error(e, m)
                        metaMap[m.key] = m.value
                    }
                })

                // Read price directly from the joined comparison
                let price = 0
                let currency = ''
                if (v.comparison) {
                    price = v.comparison.quantity_to
                    currency = v.comparison.target_value?.expression || ''
                }

                return { ...v, ...metaMap, price, currency, ref_super_values_ids: v.ref_super_values_ids ?? [] }
            })

            return items
        }
    })

    // ----- Query: fetch ingredient options -----
    const {
        data: ingredientData,
        isLoading: isIngredientsLoading,
        refetch: refetchIngredients
    } = useQuery({
        queryKey: [INGREDIENTS_KEY, fiatStore.mainFiatId],
        queryFn: async () => {

            const ingredientRes = await $fetch<{ data?: ValueRecord[] }>(`${config.public.apiBase}/values/query`, {
                method: 'POST',
                body: {
                    context: 'chinese_restaurant',
                    type: 'ingredient',
                    page_size: 200,
                    comparison: true,
                    comparison_to_id: fiatStore.mainFiatId
                }
            })

            const consumableRes = await $fetch<{ data?: ValueRecord[] }>(`${config.public.apiBase}/values/query`, {
                method: 'POST',
                body: {
                    context: 'chinese_restaurant',
                    type: 'consumable',
                    page_size: 200,
                    comparison: true,
                    comparison_to_id: fiatStore.mainFiatId
                }
            })

            const all: ValueRecord[] = [
                ...(ingredientRes?.data || []),
                ...(consumableRes?.data || [])
            ]

            const options: IngredientOption[] = all.map((i) => {
                let price = 0
                if (i.comparison) {
                    price = i.comparison.quantity_to
                }

                return {
                    label: i.name,
                    value: i.id,
                    expression: i.expression || 'unit',
                    price
                }
            })

            return options
        }
    })

    // Computed helpers
    const items = computed(() => menuData.value ?? [])
    const ingredientOptions = computed(() => ingredientData.value ?? [])
    const isLoading = computed(() => isMenuLoading.value || isIngredientsLoading.value)

    // ----- Mutation: save (create / update) -----
    const saveMutation = useMutation({
        mutationFn: async ({ editingItem, formData }: { editingItem: MenuItem | null; formData: Record<string, unknown> | { value?: unknown } }) => {
            if (editingItem) {
                const bodyPayload = 'value' in formData && formData.value ? formData.value : formData
                await $fetch(`${config.public.apiBase}/d/values_with_comparison/id/${editingItem.id}`, {
                    method: 'PUT',
                    body: bodyPayload
                })
            } else {
                await $fetch(`${config.public.apiBase}/d/values_with_comparison/`, {
                    method: 'POST',
                    body: formData
                })
            }
        },
        onSuccess: (_data, variables) => {
            queryClient.invalidateQueries({ queryKey: [MENU_KEY] })
            const action = variables.editingItem ? 'updated' : 'created'
            toast.add({ title: 'Success', description: `Dish ${action}` })
        },
        onError: (err) => {
            console.error('[useMenuQuery] Save error:', err)
            toast.add({ title: 'Error', description: 'Failed to save dish', color: 'error' })
        }
    })

    // ----- Mutation: delete -----
    const deleteMutation = useMutation({
        mutationFn: async (id: number) => {
            await $fetch(`${config.public.apiBase}/values/id/${id}`, { method: 'DELETE' })
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: [MENU_KEY] })
            toast.add({ title: 'Success', description: 'Dish deleted' })
        },
        onError: (err) => {
            console.error('[useMenuQuery] Delete error:', err)
            toast.add({ title: 'Error', description: 'Failed to delete dish', color: 'error' })
        }
    })

    function refetchAll() {
        refetchMenu()
        refetchIngredients()
    }

    return {
        // Data
        items,
        ingredientOptions,
        isLoading,
        isMenuError,
        menuError,
        // Mutations
        saveMutation,
        deleteMutation,
        // Actions
        refetchAll
    }
}
