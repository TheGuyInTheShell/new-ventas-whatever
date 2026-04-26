/**
 * @fileoverview Inventory Page Module for Chinese Restaurant.
 * 
 * This module manages the inventory state, filtering, and price calculations
 * using Alpine.js and integrates with the global fiatStore and local inventoryStore.
 */

import Alpine from "alpinejs";
import { fiatStore, fiatActions } from "../../store/fiatStore.js";
import { inventoryStore, inventoryActions } from "../../store/inventoryStore.js";
import { notifySuccess, notifyError } from "../../includes/toast.js";
import { createIcons, icons } from "lucide";
import mask from '@alpinejs/mask';
import focus from '@alpinejs/focus';
import collapse from '@alpinejs/collapse';

Alpine.plugin(mask);
Alpine.plugin(focus);
Alpine.plugin(collapse);

window.Alpine = Alpine;
/**
 * @typedef {Object} InventoryItem
 * @property {number} id - Unique identifier.
 * @property {string} uid - Unique string identifier.
 * @property {string} name - Item name.
 * @property {string} type - Item type (e.g., ingredient, utensil).
 * @property {string} expression - Unit expression (e.g., kg, units).
 * @property {string} context - Data context.
 * @property {string} identifier - Internal identifier.
 * @property {number|null} comparison_id - Associated comparison ID.
 * @property {number} quantity_from - Base quantity for price comparison.
 * @property {number} quantity_to - Target quantity/price for comparison.
 * @property {number|null} value_to - Fiat currency ID for the price.
 * @property {number} balance - Current stock quantity.
 */

document.addEventListener('alpine:init', () => {
    /**
     * Registers the 'inventoryPage' Alpine.js data component.
     */
    Alpine.data('inventoryPage', (initialItems) => ({
        /** @type {string} */
        searchQuery: '',
        /** @type {string} */
        typeFilter: 'all',
        /** @type {'asc'|'desc'} */
        sortOrder: 'asc',

        /** @type {boolean} */
        deleteModalOpen: false,
        /** @type {InventoryItem|null} */
        itemToDelete: null,

        /** @type {boolean} */
        formModalOpen: false,
        /** @type {boolean} */
        isSaving: false,
        /** @type {InventoryItem|null} */
        editingItem: null,
        /** @type {Object} */
        formData: {
            name: '',
            type: 'ingredient',
            expression: 'unit',
            price: 0,
            currency_id: null,
            ingredients: [],
            source_id: null,
            value_ratio: 0
        },

        /** @type {Object} */
        fiatContext: fiatStore.getSnapshot().context,
        /** @type {Object} */
        inventoryContext: inventoryStore.getSnapshot().context,

        /**
         * Initializes the component, subscribes to stores, and loads data if necessary.
         * @async
         */
        async init() {
            // Subscribe to fiatStore
            fiatStore.subscribe((snapshot) => {
                this.fiatContext = snapshot.context;
            });

            // Subscribe to inventoryStore
            inventoryStore.subscribe((snapshot) => {
                this.inventoryContext = snapshot.context;
            });

            // Make sure fiats are loaded if they aren't already
            if (this.fiatContext.fiats.length === 0) {
                await fiatActions.fetchFiats();
            }

            // If initial items were injected by Jinja, set them to the store
            if (initialItems && initialItems.length > 0 && this.inventoryContext.items.length === 0) {
                inventoryStore.trigger.setItems({ data: initialItems });
            } else if (this.inventoryContext.items.length === 0) {
                // Otherwise fetch from API
                await inventoryActions.fetchItems();
            }

            this.$nextTick(() => {
                createIcons({ icons });
            });

            // Watch for type changes to fetch eligible items for composition
            this.$watch('formData.type', async (newType) => {
                if (newType === 'made-from' || newType === 'by-product') {
                    if (this.inventoryContext.eligibleItems.length === 0) {
                        await inventoryActions.fetchEligibleItems();
                    }
                }
            });
        },

        /**
         * Returns a filtered and sorted list of inventory items.
         * @property {InventoryItem[]}
         */
        get filteredItems() {
            let result = [...this.inventoryContext.items];

            // Text search
            if (this.searchQuery) {
                const q = this.searchQuery.toLowerCase();
                result = result.filter(i => i.name.toLowerCase().includes(q));
            }

            // Type filter
            if (this.typeFilter !== 'all') {
                result = result.filter(i => i.type === this.typeFilter);
            }

            // Sort
            if (this.sortOrder === 'asc') {
                result.sort((a, b) => a.name.localeCompare(b.name));
            } else {
                result.sort((a, b) => b.name.localeCompare(a.name));
            }

            return result;
        },

        /**
         * Toggles the sort order between ascending and descending.
         */
        toggleSort() {
            this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
            this.$nextTick(() => {
                createIcons({ icons });
            });
        },

        /**
         * Returns the symbol/expression of the main fiat currency.
         * @returns {string}
         */
        getMainFiatExpression() {
            const mainId = this.fiatContext.mainFiatId;
            if (!mainId) return '';
            const fiat = this.fiatContext.fiats.find(f => f.id === mainId);
            return fiat ? fiat.expression : '';
        },

        /**
         * Returns the name of the main fiat currency.
         * @returns {string}
         */
        getMainFiatName() {
            const mainId = this.fiatContext.mainFiatId;
            if (!mainId) return '';
            const fiat = this.fiatContext.fiats.find(f => f.id === mainId);
            return fiat ? fiat.name : '';
        },

        /**
         * Calculates the price of an item converted to the main fiat currency.
         * @param {InventoryItem} item - The inventory item to calculate.
         * @returns {number|string}
         */
        calculatePrice(item) {
            if (!item.quantity_to || item.quantity_to <= 0) return '-';

            const mainId = this.fiatContext.mainFiatId;
            if (!mainId) return item.quantity_to;

            let price = item.quantity_to / item.quantity_from;

            // If the value_to of this item is NOT the main fiat, we convert it using exchangeRates
            if (item.value_to && item.value_to !== mainId) {
                const rate = this.fiatContext.exchangeRates[item.value_to];
                if (rate) {
                    // Conversion logic: rate expresses how much 1 main fiat is in the target fiat
                    // To convert Target to Main: Target / rate
                    price = price / rate;
                }
            }

            return parseFloat(price.toFixed(2));
        },

        /**
         * Opens the modal to add a new inventory item.
         */
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

        /**
         * Opens the modal to edit an existing inventory item.
         * @param {InventoryItem} item - The item to edit.
         */
        editItem(item) {
            this.editingItem = item;
            this.formData = {
                name: item.name,
                type: item.type,
                expression: item.expression,
                price: item.quantity_to || 0,
                currency_id: item.value_to || this.fiatContext.mainFiatId,
                ingredients: item.type === 'made-from' ? item.ref_super_values_ids : [],
                source_id: item.type === 'by-product' ? item.ref_super_values_ids[0] : null,
                value_ratio: item.type === 'by-product' ? (item.meta.find(m => m.key === 'value_ratio')?.value || 0) : 0
            };
            this.formModalOpen = true;
            this.$nextTick(() => { createIcons({ icons }); });
        },

        /**
         * Closes the form modal.
         */
        closeFormModal() {
            this.formModalOpen = false;
        },

        /**
         * Opens the modal to adjust stock for an item.
         * @param {InventoryItem} item - The item to adjust.
         */
        openAdjustModal(item) {
            console.log('Adjust Stock', item);
        },

        /**
         * Submits a save action for an item via the inventory store.
         * @async
         */
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
            } catch (e) {
                notifyError(e.message || 'Unknown error', 'Error');
            } finally {
                this.isSaving = false;
            }
        },

        /**
         * Opens the delete confirmation modal.
         * @param {InventoryItem} item - The item to delete.
         */
        openDeleteModal(item) {
            this.itemToDelete = item;
            this.deleteModalOpen = true;
        },

        /**
         * Confirms and executes the deletion of the selected item.
         * @async
         */
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