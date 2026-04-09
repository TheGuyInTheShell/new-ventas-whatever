// Type augmentation for @tanstack/vue-table
// This helps TypeScript find the module when pnpm hoisting isn't perfect
import * as VueTable from '@tanstack/vue-table'

declare module '@tanstack/vue-table' {
    export * from VueTable
}
