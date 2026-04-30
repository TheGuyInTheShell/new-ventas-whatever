import Alpine from "alpinejs";
import { fiatStore, fiatActions } from "../../store/fiatStore";
import { inventoryStore, inventoryActions } from "../../store/inventoryStore";
import { notifySuccess, notifyError } from "../../includes/toast";
import { createIcons, icons } from "lucide";
import mask from '@alpinejs/mask';
import focus from '@alpinejs/focus';
import collapse from '@alpinejs/collapse';
import { InventoryItem } from "../../types/inventory";

Alpine.plugin(mask);
Alpine.plugin(focus);
Alpine.plugin(collapse);

(window as any).Alpine = Alpine;

document.addEventListener('alpine:init', () => {
    Alpine.data('inventoryPage', (initialItems: InventoryItem[]) => ({
        searchQuery: '',
        typeFilter: 'all',
        sortOrder: 'asc' as 'asc' | 'desc',

        deleteModalOpen: false,
        itemToDelete: null as InventoryItem | null,

        formModalOpen: false,
        isSaving: false,
        editingItem: null as InventoryItem | null,
        formData: {
            name: '',
            type: 'ingredient',
            expression: 'unit',
            price: 0,
            currency_id: null as number | null,
            ingredients: [] as string[],
            source_id: null as string | null,
            value_ratio: 0
        },

        fiatContext: fiatStore.getSnapshot().context,
        inventoryContext: inventoryStore.getSnapshot().context,

        async init() {
            fiatStore.subscribe((snapshot) => {
                this.fiatContext = snapshot.context;
            });

            inventoryStore.subscribe((snapshot) => {
                this.inventoryContext = snapshot.context;
            });

            if (this.fiatContext.fiats.length === 0) {
                await fiatActions.fetchFiats();
            }

            if (initialItems && initialItems.length > 0 && this.inventoryContext.items.length === 0) {
                inventoryStore.trigger.setItems({ data: initialItems });
            } else if (this.inventoryContext.items.length === 0) {
                await inventoryActions.fetchItems();
            }

            this.$nextTick(() => {
                createIcons({ icons });
            });

            this.$watch('formData.type', async (newType: string) => {
                if (newType === 'made-from' || newType === 'by-product') {
                    if (this.inventoryContext.eligibleItems.length === 0) {
                        await inventoryActions.fetchEligibleItems();
                    }
                }
            });
        },

        get filteredItems(): InventoryItem[] {
            let result = [...this.inventoryContext.items];

            if (this.searchQuery) {
                const q = this.searchQuery.toLowerCase();
                result = result.filter(i => i.name.toLowerCase().includes(q));
            }

            if (this.typeFilter !== 'all') {
                result = result.filter(i => i.type === this.typeFilter);
            }

            if (this.sortOrder === 'asc') {
                result.sort((a, b) => a.name.localeCompare(b.name));
            } else {
                result.sort((a, b) => b.name.localeCompare(a.name));
            }

            return result;
        },

        toggleSort() {
            this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
            this.$nextTick(() => {
                createIcons({ icons });
            });
        },

        getMainFiatExpression(): string {
            const mainId = this.fiatContext.mainFiatId;
            if (!mainId) return '';
            const fiat = this.fiatContext.fiats.find(f => f.id === mainId);
            return fiat ? fiat.expression : '';
        },

        getMainFiatName(): string {
            const mainId = this.fiatContext.mainFiatId;
            if (!mainId) return '';
            const fiat = this.fiatContext.fiats.find(f => f.id === mainId);
            return fiat ? fiat.name : '';
        },

        calculatePrice(item: InventoryItem): number | string {
            if (!item.quantity_to || item.quantity_to <= 0) return '-';

            const mainId = this.fiatContext.mainFiatId;
            if (!mainId) return item.quantity_to;

            let price = item.quantity_to / item.quantity_from;

            if (item.value_to && item.value_to !== mainId) {
                const rate = this.fiatContext.exchangeRates[item.value_to];
                if (rate) {
                    price = price / rate;
                }
            }

            return parseFloat(price.toFixed(2));
        },

        openAddModal() {
            this.editingItem = null;
            this.formData = {
                name: '',
                type: 'ingredient',
                expression: 'unit',
                price: 0,
                currency_id: this.fiatContext.mainFiatId,
                ingredients: [],
                source_id: null,
                value_ratio: 0
            };
            this.formModalOpen = true;
            this.$nextTick(() => { createIcons({ icons }); });
        },

        editItem(item: InventoryItem) {
            this.editingItem = item;
            this.formData = {
                name: item.name,
                type: item.type,
                expression: item.expression,
                price: item.quantity_to || 0,
                currency_id: item.value_to || this.fiatContext.mainFiatId,
                ingredients: item.type === 'made-from' ? item.ref_super_values_ids.map(id => id.toString()) : [],
                source_id: item.type === 'by-product' ? item.ref_super_values_ids[0]?.toString() : null,
                value_ratio: item.type === 'by-product' ? parseFloat(item.meta.find(m => m.key === 'value_ratio')?.value || '0') : 0
            };
            this.formModalOpen = true;
            this.$nextTick(() => { createIcons({ icons }); });
        },

        closeFormModal() {
            this.formModalOpen = false;
        },

        openAdjustModal(item: InventoryItem) {
            console.log('Adjust Stock', item);
        },

        async saveItemSubmit() {
            this.isSaving = true;
            try {
                const success = await inventoryActions.saveItem(this.editingItem, this.formData);
                if (success) {
                    this.formModalOpen = false;
                    notifySuccess(this.editingItem ? 'Item updated successfully' : 'Item added successfully', 'Inventory');
                } else {
                    notifyError('Failed to save item. Check the console.', 'Error');
                }
            } catch (e: any) {
                notifyError(e.message || 'Unknown error', 'Error');
            } finally {
                this.isSaving = false;
            }
        },

        openDeleteModal(item: InventoryItem) {
            this.itemToDelete = item;
            this.deleteModalOpen = true;
        },

        async confirmDelete() {
            if (!this.itemToDelete) return;

            const success = await inventoryActions.deleteItem(this.itemToDelete.id, this.itemToDelete.comparison_id);

            if (success) {
                this.deleteModalOpen = false;
                this.itemToDelete = null;
            }
        }
    }));
});

Alpine.start();
