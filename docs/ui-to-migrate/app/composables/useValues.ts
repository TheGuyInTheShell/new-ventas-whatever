import type { Ref } from 'vue'

// Types
export interface MetaValue {
  uid: string
  id: number
  key: string
  value: string | null
}

export interface Value {
  uid: string
  id: number
  name: string
  expression: string
  meta?: MetaValue[]
}

export interface ValueListResponse {
  data: Value[]
  total: number
  page: number
  page_size: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
  next_page: number | null
  prev_page: number | null
}

export interface CreateValuePayload {
  name: string
  expression: string
  meta?: { key: string, value?: string }[]
}

// Composable
export function useValues() {
  const values: Ref<Value[]> = ref([])
  const loading = ref(false)
  const error = ref<Error | null>(null)
  const pagination = ref({
    page: 1,
    pageSize: 10,
    total: 0,
    totalPages: 1
  })

  /**
     * Fetch paginated values
     */
  async function fetchValues(page = 1, order: 'asc' | 'desc' = 'asc') {
    loading.value = true
    error.value = null

    try {
      const response = await $fetch<ValueListResponse>('/api/values', {
        query: { pag: page, ord: order }
      })

      values.value = response.data
      pagination.value = {
        page: response.page,
        pageSize: response.page_size,
        total: response.total,
        totalPages: response.total_pages
      }
    } catch (e) {
      error.value = e as Error
    } finally {
      loading.value = false
    }
  }

  /**
     * Fetch all values without pagination
     */
  async function fetchAllValues() {
    loading.value = true
    error.value = null

    try {
      const response = await $fetch<ValueListResponse>('/api/values/all')
      values.value = response.data
    } catch (e) {
      error.value = e as Error
    } finally {
      loading.value = false
    }
  }

  /**
     * Fetch a single value by ID
     */
  async function fetchValue(id: string | number) {
    loading.value = true
    error.value = null

    try {
      return await $fetch<Value>(`/api/values/${id}`)
    } catch (e) {
      error.value = e as Error
      return null
    } finally {
      loading.value = false
    }
  }

  /**
     * Create a new value
     */
  async function createValue(payload: CreateValuePayload) {
    loading.value = true
    error.value = null

    try {
      const result = await $fetch<Value>('/api/values', {
        method: 'POST',
        body: payload
      })
      // Refresh list
      await fetchValues(pagination.value.page)
      return result
    } catch (e) {
      error.value = e as Error
      return null
    } finally {
      loading.value = false
    }
  }

  /**
     * Update an existing value
     */
  async function updateValue(id: string | number, payload: CreateValuePayload) {
    loading.value = true
    error.value = null

    try {
      const result = await $fetch<Value>(`/api/values/${id}`, {
        method: 'PUT',
        body: payload
      })
      // Refresh list
      await fetchValues(pagination.value.page)
      return result
    } catch (e) {
      error.value = e as Error
      return null
    } finally {
      loading.value = false
    }
  }

  /**
     * Delete a value
     */
  async function deleteValue(id: string | number) {
    loading.value = true
    error.value = null

    try {
      await $fetch(`/api/values/${id}`, { method: 'DELETE' })
      // Refresh list
      await fetchValues(pagination.value.page)
      return true
    } catch (e) {
      error.value = e as Error
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    values,
    loading,
    error,
    pagination,
    fetchValues,
    fetchAllValues,
    fetchValue,
    createValue,
    updateValue,
    deleteValue
  }
}
