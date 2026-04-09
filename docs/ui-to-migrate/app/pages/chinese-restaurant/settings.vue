<script setup lang="ts">
import { useBusinessEntityStore, type BusinessEntity, type BusinessEntityGroup } from '~/stores/useBusinessEntityStore'

const toast = useToast()
const store = useBusinessEntityStore()

// ── Tab state ──────────────────────────────────────────────────────────────
const activeTab = ref(0)
const tabs = [
    { label: 'Entities', icon: 'i-lucide-building-2' },
    { label: 'Hierarchy', icon: 'i-lucide-git-branch' },
]

// ── Constants ──────────────────────────────────────────────────────────────
const ENTITY_TYPES = [
    { label: 'Restaurant',  value: 'restaurant' },
    { label: 'Bank',        value: 'bank'       },
    { label: 'Provider',    value: 'provider'    },
    { label: 'Custom',      value: 'custom'      },
]

// ── Entity state ───────────────────────────────────────────────────────────
const entities  = ref<BusinessEntity[]>([])
const groups    = ref<BusinessEntityGroup[]>([])
const loading   = ref(false)

// Create entity modal
const isCreateOpen = ref(false)
const createForm = reactive({
    name: '',
    type: 'restaurant',
    context: '',
    metadata_info: '{}',
})

// Edit entity modal
const isEditOpen = ref(false)
const editingEntity = ref<BusinessEntity | null>(null)
const editForm = reactive({
    name: '',
    type: '',
    context: '',
    metadata_info: '{}',
})

// Create group modal
const isGroupCreateOpen = ref(false)
const groupForm = reactive({
    ref_entity_top: null as number | null,
    ref_entity_bottom: null as number | null,
})

// ── Entity table columns ───────────────────────────────────────────────────
const entityColumns: any[] = [
    { accessorKey: 'id',            header: 'ID'      },
    { accessorKey: 'name',          header: 'Name'    },
    { accessorKey: 'type',          header: 'Type'    },
    { accessorKey: 'context',       header: 'Context' },
    { accessorKey: 'actions',       header: ''        },
]

// ── Lifecycle ──────────────────────────────────────────────────────────────
onMounted(loadAll)

async function loadAll() {
    loading.value = true
    try {
        const [e, g] = await Promise.all([
            store.fetchEntities(),
            store.fetchGroups(),
        ])
        entities.value = e
        groups.value = g
    } finally {
        loading.value = false
    }
}

// ── Entity CRUD ────────────────────────────────────────────────────────────
function openCreateEntity() {
    createForm.name = ''
    createForm.type = 'restaurant'
    createForm.context = ''
    createForm.metadata_info = '{}'
    isCreateOpen.value = true
}

async function saveCreateEntity() {
    if (!createForm.name.trim()) {
        toast.add({ title: 'Validation', description: 'Name is required', color: 'warning' })
        return
    }
    let meta: Record<string, any> | undefined
    try {
        meta = JSON.parse(createForm.metadata_info)
    } catch {
        toast.add({ title: 'Validation', description: 'Invalid JSON in metadata', color: 'warning' })
        return
    }
    try {
        await store.createEntity({
            name:          createForm.name.trim(),
            type:          createForm.type,
            context:       createForm.context.trim() || undefined,
            metadata_info: Object.keys(meta!).length ? meta : undefined,
        })
        toast.add({ title: 'Success', description: 'Entity created' })
        isCreateOpen.value = false
        await reloadEntities()
    } catch {
        toast.add({ title: 'Error', description: 'Failed to create entity', color: 'error' })
    }
}

function openEditEntity(entity: BusinessEntity) {
    editingEntity.value = entity
    editForm.name          = entity.name
    editForm.type          = entity.type ?? ''
    editForm.context       = entity.context ?? ''
    editForm.metadata_info = entity.metadata_info ? JSON.stringify(entity.metadata_info, null, 2) : '{}'
    isEditOpen.value       = true
}

async function saveEditEntity() {
    if (!editingEntity.value) return
    let meta: Record<string, any> | undefined
    try {
        meta = JSON.parse(editForm.metadata_info)
    } catch {
        toast.add({ title: 'Validation', description: 'Invalid JSON in metadata', color: 'warning' })
        return
    }
    const result = await store.updateEntity(editingEntity.value.id, {
        name:          editForm.name.trim(),
        type:          editForm.type,
        context:       editForm.context.trim() || undefined,
        metadata_info: Object.keys(meta!).length ? meta : undefined,
    })
    if (result) {
        toast.add({ title: 'Success', description: 'Entity updated' })
        isEditOpen.value = false
        await reloadEntities()
    }
}

async function handleDeleteEntity(entity: BusinessEntity) {
    if (!confirm(`Delete "${entity.name}"?`)) return
    const ok = await store.deleteEntity(entity.id)
    if (ok) {
        toast.add({ title: 'Success', description: 'Entity deleted' })
        await reloadEntities()
    }
}

async function reloadEntities() {
    entities.value = await store.fetchEntities()
}

// ── Group CRUD ─────────────────────────────────────────────────────────────
function openCreateGroup() {
    groupForm.ref_entity_top = null
    groupForm.ref_entity_bottom = null
    isGroupCreateOpen.value = true
}

async function saveCreateGroup() {
    if (!groupForm.ref_entity_top || !groupForm.ref_entity_bottom) {
        toast.add({ title: 'Validation', description: 'Select both parent and child entities', color: 'warning' })
        return
    }
    if (groupForm.ref_entity_top === groupForm.ref_entity_bottom) {
        toast.add({ title: 'Validation', description: 'Parent and child must be different', color: 'warning' })
        return
    }
    const result = await store.createGroup(groupForm.ref_entity_top, groupForm.ref_entity_bottom)
    if (result) {
        toast.add({ title: 'Success', description: 'Relationship created' })
        isGroupCreateOpen.value = false
        groups.value = await store.fetchGroups()
    }
}

async function handleDeleteGroup(group: BusinessEntityGroup) {
    if (!confirm('Remove this relationship?')) return
    const ok = await store.deleteGroup(group.id)
    if (ok) {
        toast.add({ title: 'Success', description: 'Relationship removed' })
        groups.value = await store.fetchGroups()
    }
}

// ── Helpers ────────────────────────────────────────────────────────────────
function entityName(id: number): string {
    return entities.value.find(e => e.id === id)?.name ?? `#${id}`
}

const entityOptions = computed(() =>
    entities.value.map(e => ({ label: `${e.name} (${e.type ?? 'n/a'})`, value: e.id }))
)
</script>

<template>
  <div class="p-4 space-y-4 w-full">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold">Business Entities Settings</h1>
        <p class="text-gray-500 text-sm">Configure entities, banks, providers and their hierarchies.</p>
      </div>
    </div>

    <!-- Tabs -->
    <UTabs
      :items="tabs"
      v-model="activeTab"
      class="w-full"
    >
      <template #default="{ item, index }">
        <span class="flex items-center gap-2">
          <UIcon :name="item.icon" class="size-4" />
          {{ item.label }}
        </span>
      </template>
    </UTabs>

    <!-- ── TAB 1: Entities ─────────────────────────────────────────── -->
    <div v-show="activeTab === 0" class="space-y-4">
      <div class="flex justify-end">
        <UButton
          icon="i-lucide-plus"
          label="New Entity"
          color="primary"
          @click="openCreateEntity"
        />
      </div>

      <UTable :data="entities" :columns="entityColumns" :loading="loading">
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton
              icon="i-lucide-edit"
              variant="ghost"
              color="neutral"
              size="xs"
              @click="openEditEntity(row.original)"
            />
            <UButton
              icon="i-lucide-trash-2"
              variant="ghost"
              color="error"
              size="xs"
              @click="handleDeleteEntity(row.original)"
            />
          </div>
        </template>
      </UTable>
    </div>

    <!-- ── TAB 2: Hierarchy ────────────────────────────────────────── -->
    <div v-show="activeTab === 1" class="space-y-4">
      <div class="flex justify-end">
        <UButton
          icon="i-lucide-plus"
          label="Add Relationship"
          color="primary"
          @click="openCreateGroup"
        />
      </div>

      <!-- Groups list -->
      <div v-if="groups.length === 0 && !loading" class="text-center py-10 text-gray-400">
        <UIcon name="i-lucide-git-branch" class="size-10 mx-auto mb-2 opacity-40" />
        <p>No hierarchies defined yet.</p>
      </div>

      <div class="grid gap-3" v-else>
        <UCard v-for="group in groups" :key="group.id">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <UBadge color="primary" variant="subtle" size="sm">
                {{ entityName(group.ref_entity_top) }}
              </UBadge>
              <UIcon name="i-lucide-arrow-right" class="size-4 text-gray-400" />
              <UBadge color="neutral" variant="subtle" size="sm">
                {{ entityName(group.ref_entity_bottom) }}
              </UBadge>
            </div>
            <UButton
              icon="i-lucide-trash-2"
              variant="ghost"
              color="error"
              size="xs"
              @click="handleDeleteGroup(group)"
            />
          </div>
        </UCard>
      </div>
    </div>

    <!-- ── Create Entity Modal ─────────────────────────────────────── -->
    <UModal v-model="isCreateOpen">
      <UCard :ui="{ header: 'flex justify-between items-center' }">
        <template #header>
          <h3 class="text-lg font-bold">New Business Entity</h3>
          <UButton icon="i-lucide-x" variant="ghost" @click="isCreateOpen = false" />
        </template>

        <form @submit.prevent="saveCreateEntity" class="space-y-4">
          <UFormField label="Name" required>
            <UInput v-model="createForm.name" placeholder="e.g. Bank of America, Walmart…" class="w-full" />
          </UFormField>

          <UFormField label="Type">
            <USelect
              v-model="createForm.type"
              :options="ENTITY_TYPES"
              value-key="value"
              label-key="label"
              class="w-full"
            />
          </UFormField>

          <UFormField label="Context" help="Logical grouping key (e.g. chinese_restaurant)">
            <UInput v-model="createForm.context" placeholder="e.g. chinese_restaurant" class="w-full" />
          </UFormField>

          <UFormField label="Metadata (JSON)">
            <UTextarea
              v-model="createForm.metadata_info"
              placeholder='{ "currency": "USD" }'
              :rows="3"
              class="w-full font-mono text-xs"
            />
          </UFormField>

          <div class="flex justify-end gap-2 pt-2">
            <UButton label="Cancel" variant="ghost" color="neutral" @click="isCreateOpen = false" />
            <UButton label="Create" type="submit" color="primary" />
          </div>
        </form>
      </UCard>
    </UModal>

    <!-- ── Edit Entity Modal ───────────────────────────────────────── -->
    <UModal v-model="isEditOpen">
      <UCard :ui="{ header: 'flex justify-between items-center' }">
        <template #header>
          <h3 class="text-lg font-bold">Edit Entity</h3>
          <UButton icon="i-lucide-x" variant="ghost" @click="isEditOpen = false" />
        </template>

        <form @submit.prevent="saveEditEntity" class="space-y-4">
          <UFormField label="Name" required>
            <UInput v-model="editForm.name" class="w-full" />
          </UFormField>

          <UFormField label="Type">
            <USelect
              v-model="editForm.type"
              :options="ENTITY_TYPES"
              value-key="value"
              label-key="label"
              class="w-full"
            />
          </UFormField>

          <UFormField label="Context">
            <UInput v-model="editForm.context" class="w-full" />
          </UFormField>

          <UFormField label="Metadata (JSON)">
            <UTextarea
              v-model="editForm.metadata_info"
              :rows="3"
              class="w-full font-mono text-xs"
            />
          </UFormField>

          <div class="flex justify-end pt-2">
            <UButton label="Save" type="submit" color="primary" />
          </div>
        </form>
      </UCard>
    </UModal>

    <!-- ── Create Group Modal ──────────────────────────────────────── -->
    <UModal v-model="isGroupCreateOpen">
      <UCard :ui="{ header: 'flex justify-between items-center' }">
        <template #header>
          <h3 class="text-lg font-bold">Add Hierarchy Relationship</h3>
          <UButton icon="i-lucide-x" variant="ghost" @click="isGroupCreateOpen = false" />
        </template>

        <form @submit.prevent="saveCreateGroup" class="space-y-4">
          <UFormField label="Parent Entity" required>
            <USelect
              v-model="groupForm.ref_entity_top"
              :options="entityOptions"
              value-key="value"
              label-key="label"
              placeholder="Select parent..."
              class="w-full"
            />
          </UFormField>

          <UFormField label="Child Entity" required>
            <USelect
              v-model="groupForm.ref_entity_bottom"
              :options="entityOptions"
              value-key="value"
              label-key="label"
              placeholder="Select child..."
              class="w-full"
            />
          </UFormField>

          <p class="text-xs text-gray-400">
            Example: <strong>providers → walmart</strong>, <strong>bank → checking account</strong>
          </p>

          <div class="flex justify-end gap-2 pt-2">
            <UButton label="Cancel" variant="ghost" color="neutral" @click="isGroupCreateOpen = false" />
            <UButton label="Create" type="submit" color="primary" />
          </div>
        </form>
      </UCard>
    </UModal>
  </div>
</template>
