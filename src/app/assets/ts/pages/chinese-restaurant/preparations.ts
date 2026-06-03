import Alpine from "alpinejs";
import { fiatStore, fiatActions } from "../../store/fiatStore";
import { preparationsStore, preparationsActions } from "../../store/preparationsStore";
import { notifySuccess, notifyError } from "../../includes/toast";
import { createIcons, icons } from "lucide";
import mask from '@alpinejs/mask';
import focus from '@alpinejs/focus';
import collapse from '@alpinejs/collapse';
import { InventoryItem, InventoryStoreContext } from "../../types/inventory";
import { FiatStoreContext } from "../../types/fiat";

type DecoratorOperation = 'percentage' | 'addition' | 'subtraction' | 'multiplication';

interface ComponentDecorator {
    name: string;
    type: DecoratorOperation;
    quantity: number;
}

interface RecipeComponent {
    parent_value_id: number;
    quantity: number;
    decorators: ComponentDecorator[];
}

Alpine.plugin(mask);
Alpine.plugin(focus);
Alpine.plugin(collapse);

window.Alpine = Alpine;

document.addEventListener('alpine:init', () => {
    Alpine.data('preparationsPage', (initialItems: InventoryItem[]) => ({
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
            type: 'made-from',
            expression: 'unit',
            price: 0,
            currency_id: null as number | null,
            ingredients: [] as string[],
            source_id: null as string | null,
            value_ratio: 0
        },

        // Recipe/BOM Management
        recipeModalOpen: false,
        recipeItem: null as InventoryItem | null,
        recipeComponents: [] as RecipeComponent[],
        selectedNewComponentId: '' as string | number,

        // Per-component decorator sub-modal
        decoratorModalOpen: false,
        decoratorComponentIndex: -1,
        decoratorDraft: { name: '', type: 'percentage' as DecoratorOperation, quantity: 0 },

        // Form: initial component selectors (pre-populate on save)
        formSelectedByProductSourceId: null as number | null,
        formSelectedMadeFromIds: [] as number[],

        fiatContext: fiatStore.getSnapshot().context,
        preparationsContext: preparationsStore.getSnapshot().context,
        viewFiatId: null as number | null,

        async init() {
            fiatStore.subscribe((snapshot: { context: FiatStoreContext }) => {
                this.fiatContext = snapshot.context;
            });

            preparationsStore.subscribe((snapshot: { context: InventoryStoreContext }) => {
                this.preparationsContext = snapshot.context;
            });

            if (this.fiatContext.fiats.length === 0) {
                try {
                    await fiatActions.fetchFiats();
                } catch (e) {
                    const msg = e instanceof Error ? e.message : 'Unknown error';
                    notifyError(`Failed to load currency data: ${msg}`, 'Error');
                }
            }

            if (!this.viewFiatId) {
                this.viewFiatId = this.fiatContext.mainFiatId;
            }

            if (initialItems && initialItems.length > 0 && this.preparationsContext.items.length === 0) {
                preparationsStore.trigger.setItems({ data: initialItems });
            } else if (this.preparationsContext.items.length === 0) {
                try {
                    await preparationsActions.fetchItems();
                } catch (e) {
                    const msg = e instanceof Error ? e.message : 'Unknown error';
                    notifyError(`Failed to load inventory items: ${msg}`, 'Error');
                }
            }

            // Always fetch eligible items to support BOM dropdown selection
            try {
                await preparationsActions.fetchEligibleItems();
            } catch (e) {
                console.error("Failed to prefetch eligible items:", e);
            }

            this.$nextTick(() => {
                createIcons({ icons });
            });
        },

        get filteredItems(): InventoryItem[] {
            let result = [...this.preparationsContext.items];

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

        get eligibleForRecipe(): InventoryItem[] {
            if (!this.recipeItem) return [];
            return this.preparationsContext.eligibleItems.filter(i => i.id !== this.recipeItem!.id);
        },

        toggleSort() {
            this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
            this.$nextTick(() => {
                createIcons({ icons });
            });
        },

        getViewFiatExpression(): string {
            const fiatId = this.viewFiatId || this.fiatContext.mainFiatId;
            if (!fiatId) return '';
            const fiat = this.fiatContext.fiats.find((f: any) => f.id === fiatId);
            return fiat ? (fiat as any).expression : '';
        },

        getMainFiatName(): string {
            const mainId = this.fiatContext.mainFiatId;
            if (!mainId) return '';
            const fiat = this.fiatContext.fiats.find((f: any) => f.id === mainId);
            return fiat ? (fiat as any).name : '';
        },

        getComponentName(parentId: number): string {
            const item = this.preparationsContext.eligibleItems.find(i => i.id === parentId);
            return item ? item.name : `Item #${parentId}`;
        },

        getComponentExpression(parentId: number): string {
            const item = this.preparationsContext.eligibleItems.find(i => i.id === parentId);
            return item ? item.expression : '';
        },

        calculatePrice(item: InventoryItem): number | string {
            if (!item.quantity_to || item.quantity_to <= 0) return '-';

            const viewId = this.viewFiatId || this.fiatContext.mainFiatId;
            if (!viewId) return item.quantity_to;

            if (item.prices && item.prices.length > 0) {
                const exactMatch = item.prices.find(p => p.fiat_id === viewId);
                if (exactMatch) {
                    return parseFloat((exactMatch.quantity_to / exactMatch.quantity_from).toFixed(2));
                }
            }

            let price = item.quantity_to / item.quantity_from;

            if (item.value_to && item.value_to !== viewId) {
                const mainId = this.fiatContext.mainFiatId;
                if (!mainId) return '-';

                let priceInMain = price;
                if (item.value_to !== mainId) {
                    const rateToMain = this.fiatContext.exchangeRates[item.value_to];
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
            this.formSelectedByProductSourceId = null;
            this.formSelectedMadeFromIds = [];
            this.formData = {
                name: '',
                type: 'made-from',
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
            // Pre-populate form selectors from existing components
            if (item.type === 'by-product' && item.components && item.components.length > 0) {
                this.formSelectedByProductSourceId = item.components[0].parent_value_id;
            } else {
                this.formSelectedByProductSourceId = null;
            }
            if (item.type === 'made-from' && item.components) {
                this.formSelectedMadeFromIds = item.components.map(c => c.parent_value_id);
            } else {
                this.formSelectedMadeFromIds = [];
            }
            this.formData = {
                name: item.name,
                type: item.type,
                expression: item.expression,
                price: item.quantity_to || 0,
                currency_id: item.value_to || this.fiatContext.mainFiatId,
                ingredients: item.type === 'made-from' ? item.ref_super_values_ids.map(id => id.toString()) : [],
                source_id: item.type === 'by-product' ? item.ref_super_values_ids[0]?.toString() : null,
                value_ratio: item.type === 'by-product' ? parseFloat(item.meta?.find(m => m.key === 'value_ratio')?.value || '0') : 0
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
                const success = await preparationsActions.adjustStock(
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
                // Build initial components from form-level selectors (quantity defaults to 1, decorators empty)
                let initialComponents: RecipeComponent[] = [];

                if (this.formData.type === 'by-product' && this.formSelectedByProductSourceId) {
                    const existing = this.editingItem?.components?.find(
                        c => c.parent_value_id === this.formSelectedByProductSourceId
                    );
                    initialComponents = [{
                        parent_value_id: this.formSelectedByProductSourceId,
                        quantity: existing?.quantity ?? 1,
                        decorators: existing?.decorators ?? []
                    }];
                } else if (this.formData.type === 'made-from' && this.formSelectedMadeFromIds.length > 0) {
                    initialComponents = this.formSelectedMadeFromIds.map(id => {
                        const existing = this.editingItem?.components?.find(c => c.parent_value_id === id);
                        return {
                            parent_value_id: id,
                            quantity: existing?.quantity ?? 1,
                            decorators: existing?.decorators ?? []
                        };
                    });
                } else {
                    // Preserve existing components if no selector was used
                    initialComponents = (this.editingItem?.components ?? []).map(c => ({
                        parent_value_id: c.parent_value_id,
                        quantity: c.quantity,
                        decorators: c.decorators ?? []
                    }));
                }

                const success = await preparationsActions.saveItem({
                    ...this.editingItem,
                    ...this.formData,
                    value_to: this.formData.currency_id,
                    components: initialComponents.length > 0 ? initialComponents : null
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

        // Recipe Modal Handlers
        openRecipeModal(item: InventoryItem) {
            this.recipeItem = item;
            this.recipeComponents = item.components
                ? item.components.map(c => ({
                    parent_value_id: c.parent_value_id,
                    quantity: c.quantity,
                    decorators: c.decorators ? c.decorators.map(d => ({ ...d })) : []
                }))
                : [];
            this.selectedNewComponentId = '';
            this.decoratorModalOpen = false;
            this.decoratorComponentIndex = -1;
            this.recipeModalOpen = true;
        },

        // Decorator sub-modal handlers
        openDecoratorModal(index: number) {
            this.decoratorComponentIndex = index;
            this.decoratorDraft = { name: '', type: 'percentage', quantity: 0 };
            this.decoratorModalOpen = true;
            this.$nextTick(() => { createIcons({ icons }); });
        },

        closeDecoratorModal() {
            this.decoratorModalOpen = false;
            this.decoratorComponentIndex = -1;
        },

        addDecorator() {
            const i = this.decoratorComponentIndex;
            if (i < 0 || !this.decoratorDraft.name.trim()) return;
            if (!this.recipeComponents[i].decorators) {
                this.recipeComponents[i].decorators = [];
            }
            this.recipeComponents[i].decorators!.push({ ...this.decoratorDraft });
            this.decoratorModalOpen = false;
        },

        removeDecorator(componentIndex: number, decoratorIndex: number) {
            this.recipeComponents[componentIndex].decorators!.splice(decoratorIndex, 1);
            this.$nextTick(() => { createIcons({ icons }); });
        },

        closeRecipeModal() {
            this.recipeModalOpen = false;
        },

        addRecipeComponent() {
            const parentId = parseInt(this.selectedNewComponentId.toString());
            if (!parentId) return;
            if (this.recipeComponents.some(c => c.parent_value_id === parentId)) {
                notifyError('Component is already in this recipe', 'Recipe');
                return;
            }
            this.recipeComponents.push({
                parent_value_id: parentId,
                quantity: 1.0,
                decorators: []
            });
            this.selectedNewComponentId = '';
            this.$nextTick(() => { createIcons({ icons }); });
        },

        removeRecipeComponent(index: number) {
            this.recipeComponents.splice(index, 1);
        },

        async saveRecipeSubmit() {
            if (!this.recipeItem) return;
            this.isSaving = true;
            try {
                const success = await preparationsActions.saveItem({
                    id: this.recipeItem.id,
                    uid: this.recipeItem.uid,
                    name: this.recipeItem.name,
                    type: this.recipeItem.type,
                    expression: this.recipeItem.expression,
                    quantity_from: this.recipeItem.quantity_from,
                    quantity_to: this.recipeItem.quantity_to,
                    value_to: this.recipeItem.value_to,
                    components: this.recipeComponents
                });
                if (success) {
                    this.recipeModalOpen = false;
                    notifySuccess('Recipe updated successfully', 'Recipe');
                } else {
                    notifyError('Failed to update recipe', 'Error');
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
                const success = await preparationsActions.deleteItem(this.itemToDelete);

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
