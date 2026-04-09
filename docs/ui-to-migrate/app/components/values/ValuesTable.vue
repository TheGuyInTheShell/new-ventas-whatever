<script setup lang="ts">
import {
  createColumnHelper,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useVueTable,
  FlexRender,
  type CellContext
} from '@tanstack/vue-table'
import type { Value, MetaValue } from '~/composables/useValues'

// Props & Emits
const props = defineProps<{
  values: Value[]
  loading?: boolean
}>()

const emit = defineEmits<{
  edit: [value: Value]
  delete: [value: Value]
}>()

// Column definitions using TanStack Table
const columnHelper = createColumnHelper<Value>()

const columns = [
  columnHelper.accessor('id', {
    header: 'ID',
    cell: (info: CellContext<Value, number>) => info.getValue()
  }),
  columnHelper.accessor('name', {
    header: 'Name',
    cell: (info: CellContext<Value, string>) => info.getValue()
  }),
  columnHelper.accessor('expression', {
    header: 'Expression',
    cell: (info: CellContext<Value, string>) => h('span', { class: 'font-mono text-primary' }, info.getValue())
  }),
  columnHelper.accessor('meta', {
    header: 'Metadata',
    cell: (info) => {
      const meta = info.getValue()
      if (!meta || meta.length === 0) return '-'
      return meta.map((m: MetaValue) => `${m.key}: ${m.value}`).join(', ')
    }
  }),
  columnHelper.display({
    id: 'actions',
    header: 'Actions',
    cell: ({ row }) => h('div', { class: 'flex gap-2' }, [
      h('button', {
        class: 'text-primary hover:text-primary-600',
        onClick: () => emit('edit', row.original)
      }, 'Edit'),
      h('button', {
        class: 'text-red-500 hover:text-red-600',
        onClick: () => emit('delete', row.original)
      }, 'Delete')
    ])
  })
]

// Table instance
const table = useVueTable({
  get data() { return props.values },
  columns,
  getCoreRowModel: getCoreRowModel(),
  getSortedRowModel: getSortedRowModel(),
  getPaginationRowModel: getPaginationRowModel()
})
</script>

<template>
  <div class="space-y-4">
    <!-- Loading state -->
    <div v-if="loading" class="flex justify-center py-8">
      <UIcon name="i-lucide-loader-2" class="animate-spin text-2xl" />
    </div>

    <!-- Table -->
    <div v-else class="overflow-x-auto">
      <UTable>
        <template #header>
          <tr>
            <th
              v-for="header in table.getHeaderGroups()[0]?.headers"
              :key="header.id"
              class="px-4 py-3 text-left text-sm font-semibold"
            >
              <FlexRender
                :render="header.column.columnDef.header"
                :props="header.getContext()"
              />
            </th>
          </tr>
        </template>

        <template #body>
          <tr
            v-for="row in table.getRowModel().rows"
            :key="row.id"
            class="hover:bg-gray-50 dark:hover:bg-gray-800"
          >
            <td
              v-for="cell in row.getVisibleCells()"
              :key="cell.id"
              class="px-4 py-3 text-sm"
            >
              <FlexRender
                :render="cell.column.columnDef.cell"
                :props="cell.getContext()"
              />
            </td>
          </tr>
        </template>

        <template #empty>
          <tr>
            <td :colspan="columns.length" class="text-center py-8 text-gray-500">
              No values found. Create one to get started.
            </td>
          </tr>
        </template>
      </UTable>
    </div>

    <!-- Pagination -->
    <div v-if="values.length > 0" class="flex items-center justify-between">
      <span class="text-sm text-gray-500">
        Showing {{ table.getRowModel().rows.length }} of {{ values.length }} values
      </span>
      <div class="flex gap-2">
        <UButton
          size="sm"
          variant="outline"
          :disabled="!table.getCanPreviousPage()"
          @click="table.previousPage()"
        >
          Previous
        </UButton>
        <UButton
          size="sm"
          variant="outline"
          :disabled="!table.getCanNextPage()"
          @click="table.nextPage()"
        >
          Next
        </UButton>
      </div>
    </div>
  </div>
</template>
