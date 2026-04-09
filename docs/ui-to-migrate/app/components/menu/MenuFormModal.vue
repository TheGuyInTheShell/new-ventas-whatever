<script setup lang="ts">
import { useFiatStore } from '~/stores/useFiatStore'
import type { MenuItem, IngredientOption } from '~/composables/useMenuQuery'

const props = defineProps<{
    open: boolean
    editingItem?: MenuItem | null
    ingredientOptions?: IngredientOption[]
    saveMutation?: { 
      mutateAsync: (variables: { editingItem: MenuItem | null, formData: Record<string, unknown> | { value?: unknown } }) => Promise<void> 
    }
}>()

const emit = defineEmits(['update:open', 'saved'])

const fiatStore = useFiatStore()

const formData = reactive({
    name: '',
    image: '', // Drive image ID
    original_price: 0,
    currency_id: null as number | null,
    price_decorators: [] as { op: string, value: number, type?: string, ref: string }[],
    prep_time: '',
    ingredients: [] as { id: number, qty: number, expression: string }[]
})

const config = useRuntimeConfig()
const imageFile = ref<File | null>(null)
const isUploadingImage = ref(false)

const imagePreview = computed(() => {
    if (imageFile.value) {
        return URL.createObjectURL(imageFile.value)
    }
    if (formData.image) {
        return formData.image // imgcdn returns absolute URLs directly
    }
    return ''
})

const newDecorator = reactive({
  op: 'SUM_PERCENTAGE',
  value: 0,
  ref: ''
})

const opOptions = [
  { label: 'Add Percentage (+%)', value: 'SUM_PERCENTAGE' },
  { label: 'Add Fixed Amount (+)', value: 'SUM_FIXED' },
  { label: 'Subtract Percentage (-%)', value: 'SUBTRACT_PERCENTAGE' },
  { label: 'Subtract Fixed Amount (-)', value: 'SUBTRACT_FIXED' }
]

const mainFiatName = computed(() => {
  const fiat = fiatStore.fiats.find((f) => f.id === fiatStore.mainFiatId)
  return fiat?.name || 'Main Currency'
})

const ingredientsBasePrice = computed(() => {
  let cost = 0
  formData.ingredients.forEach(ing => {
    
    const opt = props.ingredientOptions?.find(o => o.value === ing.id)
    if (opt && opt.price) {
      cost += ing.qty * opt.price
    }
  })
  return cost
})

watch(() => formData.ingredients, () => {
  // Update original price whenever ingredients change
  formData.original_price = Number(ingredientsBasePrice.value.toFixed(2))
}, { deep: true })

const finalPrice = computed(() => {
  let p = Number(formData.original_price) || 0
  formData.price_decorators.forEach((dec) => {
    const val = Number(dec.value) || 0
    if (dec.op === 'SUM_FIXED') {
      p += val
    } else if (dec.op === 'SUM_PERCENTAGE') {
      p += p * val
    } else if (dec.op === 'SUBTRACT_FIXED') {
      p -= val
    } else if (dec.op === 'SUBTRACT_PERCENTAGE') {
      p -= p * val
    } 
    // Fallback for old saved modifiers (ADD_TAX etc)
    else if (dec.op === 'ADD_TAX' || dec.op === 'ADD_MARKUP') {
      if ('type' in dec && dec.type === 'fixed') p += val
      else p += p * val
    } else if (dec.op === 'SUBTRACT_DISCOUNT') {
      if ('type' in dec && dec.type === 'fixed') p -= val
      else p -= p * val
    }
  })
  return Math.max(0, parseFloat(p.toFixed(2)))
})

watch(() => props.editingItem, (item) => {
  imageFile.value = null
  if (item) {
    formData.name = item.name || ''

    // Extract image_id from meta_values
    const imgIdMeta = item.meta?.find((m) => m.key === 'image_id')
    formData.image = imgIdMeta?.value || ''
        
    const prepMeta = item.meta?.find((m) => m.key === 'prep_time')
    formData.prep_time = prepMeta?.value || ''

    const ingMetaStr = item.meta?.find((m) => m.key === 'ingredients')?.value
    if (ingMetaStr) {
        try {
          const parsed = JSON.parse(ingMetaStr)
          // Support transition from number[] to { id, qty, expression }[]
          if (Array.isArray(parsed) && parsed.length > 0) {
            if (typeof parsed[0] === 'number') {
              formData.ingredients = parsed.map((id: number) => {
                const opt = props.ingredientOptions?.find(o => o.value === id)
                return { id, qty: 1, expression: opt?.expression || 'unit' }
              })
            } else {
              formData.ingredients = parsed
            }
          } else {
            formData.ingredients = []
          }
        } catch(e) { formData.ingredients = [] }
    } else {
        formData.ingredients = []
    }
        
    // Extract from meta_comparison_values
    const compMetaStr = item.meta?.find((m) => m.key === 'meta_comparison_values')?.value
    if (compMetaStr) {
      try {
        const compMeta = JSON.parse(compMetaStr)
        formData.original_price = compMeta.original_price || 0
        formData.price_decorators = compMeta.price_decorators || []
      } catch (e) {
        formData.original_price = 0
        formData.price_decorators = []
      }
    } else {
      formData.original_price = item.price || 0
      formData.price_decorators = []
    }

    formData.currency_id = item.currency_id || fiatStore.mainFiatId
  } else {
    formData.name = ''
    formData.image = ''
    formData.original_price = 0
    formData.currency_id = fiatStore.mainFiatId
    formData.price_decorators = []
    formData.prep_time = ''
    formData.ingredients = []
  }
}, { immediate: true })

const isSaving = ref(false)

const handleImageUpload = (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) {
    imageFile.value = file
  }
}

const removeImage = () => {
  imageFile.value = null
  formData.image = ''
}

async function uploadImageToDrive(file: File): Promise<string> {
  const fd = new FormData()
  fd.append('file', file)
  const res = await $fetch<{ data?: { url: string } }>(`${config.public.apiBase}/images/upload?context=menu`, {
    method: 'POST',
    body: fd
  })
  // imgcdn controller returns { data: { url: ... } } instead of just an ID
  return res.data?.url || ''
}

const addDecorator = () => {
  if (newDecorator.ref && newDecorator.value >= 0) {
    formData.price_decorators.push({ ...newDecorator })
    newDecorator.ref = ''
    newDecorator.value = 0
    newDecorator.op = 'SUM_PERCENTAGE'
  }
}

const removeDecorator = (index: number) => {
  formData.price_decorators.splice(index, 1)
}

// Ingredient helpers
const selectedIngredient = ref<string | undefined>()

const availableIngredientOptions = computed(() => {
  const selected = new Set(formData.ingredients.map(i => i.id))
  return (props.ingredientOptions || []).filter(o => !selected.has(o.value))
})

function onIngredientSelected(val: string | number | undefined) {
  if (val != null && val !== '') {
    const id = Number(val)
    if (!formData.ingredients.some(i => i.id === id)) {
      const opt = props.ingredientOptions?.find(o => o.value === id)
      formData.ingredients.push({ 
        id, 
        qty: 1, 
        expression: opt?.expression || 'unit' 
      })
    }
    // Reset selection so the placeholder shows again
    nextTick(() => {
      selectedIngredient.value = undefined
    })
  }
}

function removeIngredient(index: number) {
  formData.ingredients.splice(index, 1)
}

function getIngredientLabel(id: number): string {
  return props.ingredientOptions?.find(o => o.value === id)?.label || `#${id}`
}

async function handleSave() {
  isSaving.value = true
  try {
    // Upload image to Drive first if a new file was selected
    let imageId = formData.image
    if (imageFile.value) {
      isUploadingImage.value = true
      try {
        // Use the generic name for the function, even though underneath it calls the images upload
        imageId = await uploadImageToDrive(imageFile.value)
      } catch (err: unknown) {
        // imgcdn might return 400 for duplicated upload, we can ignore or alert
        console.warn('Image upload issue:', err)
        // If it's duplicated, maybe we can't get the URL easily here unless we catch it backend.
        // Let's re-throw if it's completely broken, or fallback to the previous image
        throw err
      } finally {
        isUploadingImage.value = false
      }
    }

    // Construct payload
    // Construct the payload required by the d/values_with_comparison endpoints
    const payloadToSave = {
      value: {
        name: formData.name,
        type: 'menu',
        expression: 'unit',
        context: 'chinese_restaurant',
        meta: [
          { key: 'image_id', value: imageId },
          { key: 'prep_time', value: formData.prep_time },
          { key: 'ingredients', value: JSON.stringify(formData.ingredients) },
          { key: 'meta_comparison_values', value: JSON.stringify({
            original_price: formData.original_price,
            final_price: finalPrice.value,
            price_decorators: formData.price_decorators
          })}
        ]
      },
      comparison_value: {
        quantity_from: 1,
        quantity_to: finalPrice.value,
        value_to: formData.currency_id,
        context: 'chinese_restaurant'
      },
      // Here you can inject selected entities or a fixed one where this menu exists
      business_entity_ids: [1] 
      // ref_inventory_value_id: undefined // Set this if you want dishes to group under a specific inventory node
    }

    if (props.saveMutation) {
      await props.saveMutation.mutateAsync({
        editingItem: props.editingItem || null,
        formData: payloadToSave
      })
    } else {
      emit('saved', payloadToSave)
    }
    close()
  } catch (e) {
    console.error(e)
  } finally {
    isSaving.value = false
  }
}

function close() {
  emit('update:open', false)
}

function onBackdropClick(e: MouseEvent) {
  if (e.target === e.currentTarget) {
    close()
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="open"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
        @click="onBackdropClick"
      >
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" />

        <!-- Dialog -->
        <div class="relative w-full max-w-2xl bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden flex flex-col max-h-[90vh]" @click.stop>
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 shrink-0">
            <div class="flex items-center gap-3">
              <div class="flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10">
                <UIcon :name="editingItem ? 'i-lucide-edit' : 'i-lucide-utensils'" class="w-5 h-5 text-primary" />
              </div>
              <div>
                <h3 class="text-lg font-semibold">
                  {{ editingItem ? 'Edit Menu Item' : 'New Menu Item' }}
                </h3>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  {{ editingItem ? 'Update dish details' : 'Add to your menu' }}
                </p>
              </div>
            </div>
            <UButton
              icon="i-lucide-x"
              variant="ghost"
              color="neutral"
              size="sm"
              @click="close"
            />
          </div>

          <!-- Body -->
          <div class="overflow-y-auto p-6 space-y-6">
            <!-- Principal Content -->
            <div class="space-y-5">
              <UFormField :ui="{ wrapper: 'w-full', container: 'w-full' }" label="Item Name" required>
                <UInput :ui="{ base: 'w-full', root: 'w-full' }" v-model="formData.name" placeholder="e.g. Spring Rolls" size="lg" />
              </UFormField>

              <UFormField :ui="{ wrapper: 'w-full', container: 'w-full' }" label="Prep Time">
                <UInput :ui="{ base: 'w-full', root: 'w-full' }" v-model="formData.prep_time" placeholder="e.g. 15 min" size="lg" />
              </UFormField>

              <UFormField :ui="{ wrapper: 'w-full', container: 'w-full' }" label="Ingredients">
                <!-- Add ingredient -->
                <div class="flex items-center gap-2 mb-2">
                  <USelect
                    v-model="selectedIngredient"
                    :items="availableIngredientOptions.map(o => ({ label: o.label, value: String(o.value) }))"
                    placeholder="Select ingredient to add..."
                    class="flex-1"
                    size="lg"
                    :ui="{ content: 'z-[100]' }"
                    @update:model-value="onIngredientSelected"
                  />
                </div>
                <!-- Selected ingredients list -->
                <div v-if="formData.ingredients.length > 0" class="space-y-2">
                  <div
                    v-for="(ing, idx) in formData.ingredients"
                    :key="ing.id"
                    class="flex items-center gap-3 bg-gray-50 dark:bg-gray-800/50 p-2.5 rounded-lg border border-gray-200 dark:border-gray-700"
                  >
                    <span class="flex-1 text-sm font-medium truncate">
                      {{ getIngredientLabel(ing.id) }}
                      <span class="ml-2 text-xs text-gray-500 font-mono">(${{ (props.ingredientOptions?.find(o => o.value === ing.id)?.price || 0).toFixed(2) }})</span>
                    </span>
                    <UInput
                      v-model.number="ing.qty"
                      type="number"
                      min="0.01"
                      step="0.01"
                      class="w-20"
                      size="sm"
                    />
                    <span>{{ ing.expression }}</span>
                    <span class="w-16 font-mono text-sm text-right text-primary-600 dark:text-primary-400">
                      ${{ ((props.ingredientOptions?.find(o => o.value === ing.id)?.price || 0) * ing.qty).toFixed(2) }}
                    </span>
                    <UButton
                      icon="i-lucide-x"
                      color="error"
                      variant="ghost"
                      size="xs"
                      @click="removeIngredient(idx)"
                    />
                  </div>
                </div>
                <p v-else class="text-xs text-gray-400 mt-1">No ingredients added yet.</p>
              </UFormField>

              <UFormField label="Dish Image">
                <div class="flex items-center gap-4">
                  <div v-if="imagePreview" class="relative w-16 h-16 rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700 shrink-0 group">
                    <img :src="imagePreview" class="w-full h-full object-cover">
                    <button
                      type="button"
                      class="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity"
                      @click="removeImage"
                    >
                      <UIcon name="i-lucide-trash" class="w-4 h-4 text-white" />
                    </button>
                  </div>
                  <div class="flex flex-col gap-1">
                    <input
                      type="file"
                      accept="image/*"
                      class="text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
                      @change="handleImageUpload"
                    >
                    <p v-if="isUploadingImage" class="text-xs text-primary flex items-center gap-1">
                      <UIcon name="i-lucide-loader-2" class="w-3 h-3 animate-spin" />
                      Uploading Image...
                    </p>
                  </div>
                </div>
              </UFormField>
            </div>

            <USeparator label="Pricing Definition" />

            <!-- Bottom Content for Pricing Details -->
            <div class="space-y-5 bg-gray-50 dark:bg-gray-800/50 p-4 rounded-xl border border-gray-100 dark:border-gray-800">
              <div class="grid grid-cols-2 gap-4">
                <UFormField label="Original Price" required>
                  <div class="flex flex-col gap-1">
                    <UInput
                      v-model="formData.original_price"
                      type="number"
                      step="0.01"
                      size="lg"
                      placeholder="10.00"
                      icon="i-lucide-dollar-sign"
                      :disabled="formData.ingredients.length > 0"
                    />
                    <span v-if="formData.ingredients.length > 0" class="text-xs text-primary-600 dark:text-primary-400">
                      Auto-calculated from ingredients
                    </span>
                  </div>
                </UFormField>
                <UFormField label="Currency" required>
                  <USelect
                    v-model="formData.currency_id"
                    :items="fiatStore.fiats.map((f) => ({ label: f.name, value: f.id }))"
                    placeholder="Select currency"
                    size="lg"
                  />
                </UFormField>
              </div>

              <div class="space-y-3 pt-2">
                <h4 class="text-sm font-medium">
                  Price Decorators (Taxes, Discounts, Margins)
                </h4>

                <div v-if="formData.price_decorators.length > 0" class="space-y-2">
                  <div v-for="(dec, idx) in formData.price_decorators" :key="idx" class="flex items-center gap-3 bg-white dark:bg-gray-900 p-2.5 rounded-lg border border-gray-200 dark:border-gray-700 text-sm">
                    <div class="flex-1 font-medium">
                      {{ dec.ref }}
                    </div>
                    <UBadge :color="dec.op.includes('SUBTRACT') ? 'success' : 'neutral'" variant="subtle">
                      {{ dec.op.replace('_', ' ') }}
                    </UBadge>
                    <div class="w-24 text-right font-mono">
                      {{ dec.op.includes('PERCENTAGE') ? (dec.value * 100).toFixed(1) + '%' : '$' + dec.value }}
                    </div>
                    <UButton
                      icon="i-lucide-trash"
                      color="error"
                      variant="ghost"
                      size="xs"
                      @click="removeDecorator(idx)"
                    />
                  </div>
                </div>

                <div class="flex items-end gap-2 bg-white dark:bg-gray-900 p-3 rounded-lg border border-gray-200 dark:border-gray-700">
                  <UFormField label="Operation" class="w-[200px]">
                    <USelect v-model="newDecorator.op" :items="opOptions" size="sm" />
                  </UFormField>
                  <UFormField label="Name/Ref" class="flex-1">
                    <UInput v-model="newDecorator.ref" placeholder="e.g. Service Fee" size="sm" />
                  </UFormField>
                  <UFormField label="Value" class="w-[100px]">
                    <UInput
                      v-model="newDecorator.value"
                      type="number"
                      step="0.01"
                      placeholder="0.15"
                      size="sm"
                    />
                  </UFormField>
                  <UButton icon="i-lucide-plus" color="neutral" @click="addDecorator" />
                </div>
                <p class="text-xs text-gray-500">
                  For percentages, enter decimal values (e.g., 0.15 for 15%).
                </p>
              </div>

              <USeparator class="my-4" />

              <div class="flex items-center justify-between p-4 bg-primary/10 rounded-xl border border-primary/20">
                <div class="text-sm font-medium text-primary-700 dark:text-primary-300">
                  Final Calculated Price
                </div>
                <div class="text-2xl font-bold font-mono text-primary-900 dark:text-primary-100">
                  {{ finalPrice.toFixed(2) }}
                  <span class="text-sm font-normal text-primary-600 dark:text-primary-400">
                    {{ 
                      Object.entries(
                        fiatStore.fiats.find((f) => f.id === formData.currency_id) || {}
                      ).map(([key, value]) => { if (key === 'expression') return `${value}`; return ''; }).join('') 
                    }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="flex justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 shrink-0">
            <UButton
              label="Cancel"
              variant="outline"
              color="neutral"
              size="lg"
              @click="close"
            />
            <UButton
              label="Save Menu Item"
              color="primary"
              size="lg"
              :loading="isSaving"
              icon="i-lucide-check"
              @click="handleSave"
            />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
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
