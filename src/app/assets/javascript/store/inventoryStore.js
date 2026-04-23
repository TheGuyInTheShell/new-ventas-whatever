import { createStore } from '@xstate/store';

/**
 * @typedef {Object} InventoryStoreContext
 * @property {Array} items - List of inventory items.
 * @property {boolean} loading - Global loading state indicator.
 * @property {string|null} error - Error message if a request fails.
 */

const API_BASE = '/api/v1';

/**
 * The XState Store instance for Inventory management.
 */
export const inventoryStore = createStore({
    context: {
        items: [],
        loading: false,
        error: null
    },
    on: {
        setLoading: (context, event) => ({ ...context, loading: event.value }),
        setItems: (context, event) => ({ ...context, items: event.data }),
        setError: (context, event) => ({ ...context, error: event.message })
    }
});

/**
 * Object containing all side-effect actions for the Inventory Store.
 */
export const inventoryActions = {
    /**
     * Fetches inventory values and comparisons from the backend.
     * @async
     * @returns {Promise<void>}
     */
    async fetchItems() {
        inventoryStore.trigger.setLoading({ value: true });
        inventoryStore.trigger.setError({ message: null });
        try {
            const res = await fetch(`${API_BASE}/values_with_comparison/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ context: 'inventory' })
            });
            const result = await res.json();

            const items = [];
            if (result.value) {
                result.value.forEach(val => {
                    const comp = result.comparison_value ? result.comparison_value.find(c => c.value_from === val.id) : null;
                    items.push({
                        id: val.id,
                        uid: val.uid,
                        name: val.name,
                        type: val.type,
                        expression: val.expression,
                        context: val.context,
                        identifier: val.identifier,
                        comparison_id: comp ? comp.id : null,
                        quantity_from: comp ? comp.quantity_from : 1,
                        quantity_to: comp ? comp.quantity_to : 0,
                        value_to: comp ? comp.value_to : null,
                        balance: 0 // Mock balance for now, expand via balances API if required
                    });
                });
            }
            inventoryStore.trigger.setItems({ data: items });
        } catch (error) {
            console.error("Failed to fetch inventory: ", error);
            inventoryStore.trigger.setError({ message: error.message || 'Unknown error' });
        } finally {
            inventoryStore.trigger.setLoading({ value: false });
        }
    },

    /**
     * Creates or updates an inventory item with its comparison data.
     * @async
     * @param {Object|null} editingItem - The item to update, or null to create.
     * @param {Object} formData - Form data (name, expression, type, price, currency_id).
     * @returns {Promise<boolean>} Success status.
     */
    async saveItem(editingItem, formData) {
        try {
            // Capitalize logically like the old Nuxt composable
            const capitalize = (s) => (s && typeof s === 'string' ? s.charAt(0).toUpperCase() + s.slice(1) : s);

            const body = {
                value: {
                    name: capitalize(formData.name),
                    expression: formData.expression,
                    type: formData.type,
                    context: 'inventory'
                },
                comparison_value: {
                    quantity_from: 1,
                    quantity_to: parseFloat(formData.price) || 0,
                    value_to: formData.currency_id || null,
                    context: 'inventory'
                },
                business_entity_ids: []
            };

            const url = editingItem
                ? `${API_BASE}/values_with_comparison/id/${editingItem.uid}`
                : `${API_BASE}/values_with_comparison/`;

            const method = editingItem ? 'PUT' : 'POST';

            const res = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            if (!res.ok) throw new Error('Failed to save');

            await this.fetchItems();
            return true;
        } catch (error) {
            console.error("Failed to save inventory item: ", error);
            inventoryStore.trigger.setError({ message: error.message || 'Failed to save item' });
            return false;
        }
    },

    /**
     * Deletes an inventory item and its associated comparison.
     * @async
     * @param {number} id - The value ID to delete.
     * @param {number} [comparisonId] - The comparison ID to delete, if any.
     * @returns {Promise<boolean>} Success status.
     */
    async deleteItem(id, comparisonId) {
        try {
            await fetch(`${API_BASE}/values/id/${id}`, { method: 'DELETE' });
            if (comparisonId) {
                await fetch(`${API_BASE}/comparison_values/id/${comparisonId}`, { method: 'DELETE' });
            }
            await this.fetchItems();
            return true;
        } catch (error) {
            console.error("Failed to delete inventory item: ", error);
            inventoryStore.trigger.setError({ message: error.message || 'Failed to delete item' });
            return false;
        }
    }
};
