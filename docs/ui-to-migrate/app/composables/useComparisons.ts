// Types
export interface ValueSimple {
  id: number
  uid: string
  name: string
  expression: string
}

export interface Comparison {
  uid: string
  id: number
  quantity_from: number
  quantity_to: number
  value_from: number
  value_to: number
  source_value?: ValueSimple
  target_value?: ValueSimple
}

export interface ComparisonListResponse {
  data: Comparison[]
  total: number
  page: number
  page_size: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

export interface ConversionResult {
  from_value: ValueSimple
  to_value: ValueSimple
  original_amount: number
  converted_amount: number
  rate: number
  inverse_rate: number
}

export interface CreateComparisonPayload {
  quantity_from: number
  quantity_to: number
  value_from: number
  value_to: number
}

export function useComparisons() {
  const comparisons = ref<Comparison[]>([])
  const loading = ref(false)
  const error = ref<Error | null>(null)

  /**
     * Fetch all comparisons
     */
  async function fetchComparisons(page = 1) {
    loading.value = true
    error.value = null

    try {
      const response = await $fetch<ComparisonListResponse>('/api/comparisons', {
        query: { pag: page }
      })
      comparisons.value = response.data
    } catch (e) {
      error.value = e as Error
    } finally {
      loading.value = false
    }
  }

  /**
     * Create a new comparison
     */
  async function createComparison(payload: CreateComparisonPayload) {
    loading.value = true
    error.value = null

    try {
      const result = await $fetch<Comparison>('/api/comparisons', {
        method: 'POST',
        body: payload
      })
      await fetchComparisons()
      return result
    } catch (e) {
      error.value = e as Error
      return null
    } finally {
      loading.value = false
    }
  }

  /**
     * Convert an amount between two values
     */
  async function convert(fromId: number, toId: number, amount: number) {
    loading.value = true
    error.value = null

    try {
      return await $fetch<ConversionResult>('/api/comparisons/convert', {
        query: { from_id: fromId, to_id: toId, amount }
      })
    } catch (e) {
      error.value = e as Error
      return null
    } finally {
      loading.value = false
    }
  }

  return {
    comparisons,
    loading,
    error,
    fetchComparisons,
    createComparison,
    convert
  }
}
