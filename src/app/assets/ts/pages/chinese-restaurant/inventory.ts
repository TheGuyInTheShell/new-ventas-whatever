import Alpine from "alpinejs";
import { fiatStore, fiatActions } from "../../store/fiatStore";
import { inventoryStore, inventoryActions } from "../../store/inventoryStore";
import { notifySuccess, notifyError } from "../../includes/toast";
import { createIcons, icons } from "lucide";
import mask from '@alpinejs/mask';
import focus from '@alpinejs/focus';
import collapse from '@alpinejs/collapse';
import { InventoryItem, InventoryStoreContext } from "../../types/inventory";
import { FiatStoreContext } from "../../types/fiat";

Alpine.plugin(mask);
Alpine.plugin(focus);
Alpine.plugin(collapse);

window.Alpine = Alpine;

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

        adjustModalOpen: false,
        isAdjusting: false,
        adjustItem: null as InventoryItem | null,
        adjustFormData: {
            new_quantity: 0,
            is_adjustment: false,
            notes: ''
        },

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
        viewFiatId: null as number | null,

        async init() {
            fiatStore.subscribe((snapshot: { context: FiatStoreContext }) => {
                const oldMainId = this.fiatContext.mainFiatId;
                this.fiatContext = snapshot.context;

                // If mainFiatId just loaded and we don't have a viewFiatId yet, sync it
                if (this.fiatContext.mainFiatId && (!this.viewFiatId || this.viewFiatId === oldMainId)) {
                    this.viewFiatId = this.fiatContext.mainFiatId;
                }
            });

            inventoryStore.subscribe((snapshot: { context: InventoryStoreContext }) => {
                this.inventoryContext = snapshot.context;
            });

            // Initial fetch
            await fiatActions.fetchFiats();

            if (!this.viewFiatId) {
                this.viewFiatId = this.fiatContext.mainFiatId;
            }

            if (initialItems && initialItems.length > 0 && this.inventoryContext.items.length === 0) {
                inventoryStore.trigger.setItems({ data: initialItems });
            } else if (this.inventoryContext.items.length === 0) {
                try {
                    await inventoryActions.fetchItems();
                } catch (e) {
                    const msg = e instanceof Error ? e.message : 'Unknown error';
                    notifyError(`Failed to load inventory items: ${msg}`, 'Error');
                }
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

        getViewFiatExpression(): string {
            const fiatId = Number(this.viewFiatId || this.fiatContext.mainFiatId);
            if (!fiatId) return '';

            const fiat = this.fiatContext.fiats.find((f: any) => Number(f.id) === fiatId);
            return fiat ? ((fiat as any).expression || (fiat as any).name || '') : '';
        },

        getMainFiatName(): string {
            const mainId = Number(this.fiatContext.mainFiatId);
            if (!mainId) return '';
            const fiat = this.fiatContext.fiats.find((f: any) => Number(f.id) === mainId);
            return fiat ? (fiat as any).name : '';
        },

        calculatePrice(item: InventoryItem): number | string {
            if (!item.quantity_to || item.quantity_to <= 0) return '-';

            const viewId = Number(this.viewFiatId || this.fiatContext.mainFiatId);
            if (!viewId) return item.quantity_to;

            // 1. Try to find an exact price match in the prices array
            if (item.prices && item.prices.length > 0) {
                const exactMatch = item.prices.find(p => Number(p.fiat_id) === viewId);
                if (exactMatch) {
                    return parseFloat((exactMatch.quantity_to / exactMatch.quantity_from).toFixed(2));
                }
            }

            // 2. Fallback to conversion logic
            let price = item.quantity_to / item.quantity_from;

            // If item primary currency is different from view currency
            const itemValueTo = Number(item.value_to);
            if (itemValueTo && itemValueTo !== viewId) {
                const mainId = Number(this.fiatContext.mainFiatId);
                if (!mainId) return '-';

                let priceInMain = price;
                if (itemValueTo !== mainId) {
                    const rateToMain = this.fiatContext.exchangeRates[itemValueTo];
                    if (rateToMain) {
                        priceInMain = price / rateToMain;
                    } else {
                        return '-';
                    }
                }

                if (viewId === mainId) {
                    price = priceInMain;
                } else {
                    const rateToView = this.fiatContext.exchangeRates[viewId];
                    if (rateToView) {
                        price = priceInMain * rateToView;
                    } else {
                        return '-';
                    }
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
            this.adjustItem = item;
            this.adjustFormData = {
                new_quantity: item.balance || 0,
                is_adjustment: false,
                notes: ''
            };
            this.adjustModalOpen = true;
            this.$nextTick(() => { createIcons({ icons }); });
        },

        closeAdjustModal() {
            this.adjustModalOpen = false;
        },

        async adjustStockSubmit() {
            if (!this.adjustItem) return;
            this.isAdjusting = true;
            try {
                const success = await inventoryActions.adjustStock(
                    this.adjustItem,
                    this.adjustFormData.new_quantity,
                    this.adjustFormData.is_adjustment,
                    this.adjustFormData.notes
                );
                if (success) {
                    this.adjustModalOpen = false;
                    notifySuccess('Stock adjusted successfully', 'Inventory');
                } else {
                    notifyError('Failed to adjust stock', 'Error');
                }
            } catch (e: any) {
                notifyError(e.message || 'Error adjusting stock', 'Error');
            } finally {
                this.isAdjusting = false;
            }
        },

        async saveItemSubmit() {
            this.isSaving = true;
            try {
                const success = await inventoryActions.saveItem({
                    ...this.editingItem,
                    ...this.formData
                });
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

            try {
                const success = await inventoryActions.deleteItem(this.itemToDelete);

                if (success) {
                    this.deleteModalOpen = false;
                    this.itemToDelete = null;
                    notifySuccess('Item deleted successfully', 'Inventory');
                } else {
                    notifyError('Failed to delete item', 'Error');
                }
            } catch (e: any) {
                notifyError(e.message || 'Error deleting item', 'Error');
            }
        }
    }));
});

Alpine.start();
