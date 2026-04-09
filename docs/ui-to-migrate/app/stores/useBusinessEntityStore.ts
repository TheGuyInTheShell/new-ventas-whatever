import { defineStore } from 'pinia'

// ─── Types ──────────────────────────────────────────────────────────────────

export interface BusinessEntityValue {
  name: string
  expression?: string
  type: string
  price?: number
  currency_id?: number | null
}

export interface BusinessEntity {
  id: number
  uid: string
  name: string
  type?: string
  context?: string
  metadata_info?: Record<string, any>
}

export interface BusinessEntityGroup {
  id: number
  ref_entity_top: number
  ref_entity_bottom: number
}

// ─── Store ───────────────────────────────────────────────────────────────────

export const useBusinessEntityStore = defineStore('businessEntity', () => {
  const config = useRuntimeConfig()
  const toast = useToast()

  const businessEntity = ref<BusinessEntity | null>(null)
  const businessEntities = ref<BusinessEntity[]>([])
  const groups = ref<BusinessEntityGroup[]>([])
  const loading = ref(false)

  // ── Low-level API helpers ──────────────────────────────────────────────

  /** Fetch a business entity by name (returns first match or null). */
  async function fetchByName(name: string): Promise<BusinessEntity | null> {
    const res: any = await $fetch(`${config.public.apiBase}/business_entities/`, {
      query: { name }
    }).catch(() => null)
    const list: BusinessEntity[] = res?.data || []
    return list.find(e => e.name === name) ?? null
  }

  /** Create a new business entity and return it. */
  async function createEntity(payload: {
    name: string
    type?: string
    context?: string
    metadata_info?: Record<string, any>
  }): Promise<BusinessEntity> {
    const result: any = await $fetch(`${config.public.apiBase}/business_entities/`, {
      method: 'POST',
      body: payload
    })
    return result as BusinessEntity
  }

  /** Upsert a business entity – creates if not found, skips if already exists. */
  async function upsertEntity(payload: {
    name: string
    type?: string
    context?: string
    metadata_info?: Record<string, any>
  }): Promise<BusinessEntity> {
    const existing = await fetchByName(payload.name)
    if (existing) return existing
    return createEntity(payload)
  }

  // ── Value helpers (bound to a context) ────────────────────────────────

  /**
     * Ensure a Value exists for a given context.
     * Creates it only if it doesn't already exist (matched by name + context).
     */
  async function upsertValue(
    context: string,
    value: BusinessEntityValue
  ): Promise<void> {
    const res: any = await $fetch(`${config.public.apiBase}/values/`, {
      query: { context, name: value.name }
    }).catch(() => null)

    const existing = (res?.data || []).find(
      (v: any) => v.name === value.name && v.context === context
    )

    if (existing) return // already seeded

    await $fetch(`${config.public.apiBase}/values/`, {
      method: 'POST',
      body: {
        name: value.name,
        expression: value.expression ?? '',
        type: value.type,
        context,
        ...(value.price !== undefined && { price: value.price }),
        ...(value.currency_id !== undefined && { currency_id: value.currency_id })
      }
    })
  }

  /**
     * Create a value for a given context (always inserts, no dedup check).
     * Useful when the caller already knows the value doesn't exist.
     */
  async function createValue(
    context: string,
    value: BusinessEntityValue
  ): Promise<void> {
    await $fetch(`${config.public.apiBase}/values/`, {
      method: 'POST',
      body: {
        name: value.name,
        expression: value.expression ?? '',
        type: value.type,
        context,
        ...(value.price !== undefined && { price: value.price }),
        ...(value.currency_id !== undefined && { currency_id: value.currency_id })
      }
    })
  }

  // ── Seed: Chinese Restaurant ───────────────────────────────────────────

  /** Seed the target business entity and its default value catalogue. */
  async function seedBusinessChineseRestaurant(): Promise<void> {
    loading.value = true
    try {
      // 1. Ensure the business entity record exists
      const entity = await upsertEntity({
        name: 'chinese-restaurant',
        type: 'restaurant',
        context: 'chinese_restaurant',
        metadata_info: {
          display_name: 'Chinese Restaurant',
          currency: 'USD'
        }
      })
      businessEntity.value = entity

      // 2. Seed default catalogue values (idempotent)
      const CONTEXT = 'chinese_restaurant'

      const defaultValues: BusinessEntityValue[] = [
        // — Menu items (type: product) —
        { name: 'Fried Rice', expression: 'plate', type: 'product', price: 8 },
        { name: 'Chow Mein', expression: 'plate', type: 'product', price: 10 },
        { name: 'Spring Rolls', expression: 'unit', type: 'product', price: 5 },
        { name: 'Sweet & Sour Pork', expression: 'plate', type: 'product', price: 12 },
        { name: 'Dim Sum', expression: 'unit', type: 'product', price: 6 },
        // — Services (type: service) —
        { name: 'Delivery Fee', expression: 'flat', type: 'service', price: 3 },
        { name: 'Table Service', expression: 'flat', type: 'service', price: 0 }
      ]

      for (const v of defaultValues) {
        await upsertValue(CONTEXT, v)
      }

      console.log('[BusinessEntity] Chinese restaurant seed complete.')
    } catch (error) {
      console.error('[BusinessEntity] Seed failed:', error)
    } finally {
      loading.value = false
    }
  }

  // ── Entity CRUD ─────────────────────────────────────────────────────────

  /** Fetch all entities, optionally filtering by context. */
  async function fetchEntities(context?: string): Promise<BusinessEntity[]> {
    loading.value = true
    try {
      const res: any = await $fetch(`${config.public.apiBase}/business_entities/`, {
        query: context ? { context } : {}
      })
      const list: BusinessEntity[] = res?.data || []
      businessEntities.value = list
      return list
    } catch (error) {
      console.error('[BusinessEntity] fetchEntities failed:', error)
      toast.add({ title: 'Error', description: 'Failed to load entities', color: 'error' })
      return []
    } finally {
      loading.value = false
    }
  }

  /** Update an existing entity by ID. */
  async function updateEntity(id: number, payload: Partial<BusinessEntity>): Promise<BusinessEntity | null> {
    try {
      const result: any = await $fetch(`${config.public.apiBase}/business_entities/id/${id}`, {
        method: 'PUT',
        body: payload
      })
      return result as BusinessEntity
    } catch (error) {
      console.error('[BusinessEntity] updateEntity failed:', error)
      toast.add({ title: 'Error', description: 'Failed to update entity', color: 'error' })
      return null
    }
  }

  /** Delete an entity by ID. */
  async function deleteEntity(id: number): Promise<boolean> {
    try {
      await $fetch(`${config.public.apiBase}/business_entities/id/${id}`, {
        method: 'DELETE'
      })
      return true
    } catch (error) {
      console.error('[BusinessEntity] deleteEntity failed:', error)
      toast.add({ title: 'Error', description: 'Failed to delete entity', color: 'error' })
      return false
    }
  }

  // ── Group CRUD ──────────────────────────────────────────────────────────

  /** Fetch all business entity groups. */
  async function fetchGroups(): Promise<BusinessEntityGroup[]> {
    try {
      const res: any = await $fetch(`${config.public.apiBase}/business_entities_groups/`)
      const list: BusinessEntityGroup[] = res?.data || []
      groups.value = list
      return list
    } catch (error) {
      console.error('[BusinessEntity] fetchGroups failed:', error)
      toast.add({ title: 'Error', description: 'Failed to load groups', color: 'error' })
      return []
    }
  }

  /** Create a new parent→child group relationship. */
  async function createGroup(ref_entity_top: number, ref_entity_bottom: number): Promise<BusinessEntityGroup | null> {
    try {
      const result: any = await $fetch(`${config.public.apiBase}/business_entities_groups/`, {
        method: 'POST',
        body: { ref_entity_top, ref_entity_bottom }
      })
      return result as BusinessEntityGroup
    } catch (error) {
      console.error('[BusinessEntity] createGroup failed:', error)
      toast.add({ title: 'Error', description: 'Failed to create group', color: 'error' })
      return null
    }
  }

  /** Delete a group relationship by ID. */
  async function deleteGroup(id: number): Promise<boolean> {
    try {
      await $fetch(`${config.public.apiBase}/business_entities_groups/id/${id}`, {
        method: 'DELETE'
      })
      return true
    } catch (error) {
      console.error('[BusinessEntity] deleteGroup failed:', error)
      toast.add({ title: 'Error', description: 'Failed to delete group', color: 'error' })
      return false
    }
  }

  return {
    businessEntity,
    businessEntities,
    groups,
    loading,
    fetchByName,
    createEntity,
    upsertEntity,
    upsertValue,
    createValue,
    fetchEntities,
    updateEntity,
    deleteEntity,
    fetchGroups,
    createGroup,
    deleteGroup,
    seedBusinessChineseRestaurant
  }
})
