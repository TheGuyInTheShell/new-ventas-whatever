<script setup lang="ts">
import type { Value } from '~/composables/useValues'

// Meta
definePageMeta({
  title: 'Values'
})

// Composables
const { values, loading, fetchValues, createValue, updateValue, deleteValue } = useValues()
const { comparisons, fetchComparisons } = useComparisons()

// UI State
const showCreateModal = ref(false)
const showEditModal = ref(false)
const editingValue = ref<Value | null>(null)
const formData = ref({
  name: '',
  expression: ''
})

// Load data on mount
onMounted(() => {
  fetchValues()
  fetchComparisons()
})

// Handlers
function openCreateModal() {
  formData.value = { name: '', expression: '' }
  showCreateModal.value = true
}

function openEditModal(value: Value) {
  editingValue.value = value
  formData.value = { name: value.name, expression: value.expression }
  showEditModal.value = true
}

async function handleCreate() {
  await createValue(formData.value)
  showCreateModal.value = false
}

async function handleUpdate() {
  if (!editingValue.value) return
  await updateValue(editingValue.value.id, formData.value)
  showEditModal.value = false
  editingValue.value = null
}

async function handleDelete(value: Value) {
  if (confirm(`Are you sure you want to delete "${value.name}"?`)) {
    await deleteValue(value.id)
  }
}
</script>

<template>
  <div class="container mx-auto px-4 py-8">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-3xl font-bold">
          Values
        </h1>
        <p class="text-gray-500 mt-1">
          Manage your universal value units
        </p>
      </div>
      <UButton
        icon="i-lucide-plus"
        color="primary"
        @click="openCreateModal"
      >
        Add Value
      </UButton>
    </div>

    <!-- Main content grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Values Table (2/3 width on large screens) -->
      <div class="lg:col-span-2">
        <div class="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <ValuesTable
            :values="values"
            :loading="loading"
            @edit="openEditModal"
            @delete="handleDelete"
          />
        </div>
      </div>

      <!-- Comparison Chart (1/3 width on large screens) -->
      <div>
        <ComparisonChart :comparisons="comparisons" />
      </div>
    </div>

    <!-- Create Modal -->
    <UModal v-model:open="showCreateModal">
      <template #header>
        <h3 class="text-lg font-semibold">
          Create New Value
        </h3>
      </template>

      <div class="p-4 space-y-4">
        <UFormField label="Name">
          <UInput v-model="formData.name" placeholder="e.g., US Dollar" />
        </UFormField>
        <UFormField label="Expression">
          <UInput v-model="formData.expression" placeholder="e.g., USD" />
        </UFormField>
      </div>

      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton variant="ghost" @click="showCreateModal = false">
            Cancel
          </UButton>
          <UButton color="primary" :loading="loading" @click="handleCreate">
            Create
          </UButton>
        </div>
      </template>
    </UModal>

    <!-- Edit Modal -->
    <UModal v-model:open="showEditModal">
      <template #header>
        <h3 class="text-lg font-semibold">
          Edit Value
        </h3>
      </template>

      <div class="p-4 space-y-4">
        <UFormField label="Name">
          <UInput v-model="formData.name" placeholder="e.g., US Dollar" />
        </UFormField>
        <UFormField label="Expression">
          <UInput v-model="formData.expression" placeholder="e.g., USD" />
        </UFormField>
      </div>

      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton variant="ghost" @click="showEditModal = false">
            Cancel
          </UButton>
          <UButton color="primary" :loading="loading" @click="handleUpdate">
            Save Changes
          </UButton>
        </div>
      </template>
    </UModal>
  </div>
</template>
