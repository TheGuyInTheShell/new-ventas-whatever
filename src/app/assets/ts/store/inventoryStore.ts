import { createStore } from '@xstate/store';
import { businessEntityStore, businessEntityActions } from './chinese-restaurant-store';
import { InventoryItem, InventoryStoreContext } from '../types/inventory';

const API_BASE = '/api/v1';

export const inventoryStore = createStore({
    context: {
        items: [] as InventoryItem[],
        eligibleItems: [] as InventoryItem[],
        loading: false,
        error: null as string | null
    } as InventoryStoreContext,
    on: {
        setLoading: (context, event: { value: boolean }) => ({ ...context, loading: event.value }),
        setItems: (context, event: { data: InventoryItem[] }) => ({ ...context, items: event.data }),
        setEligibleItems: (context, event: { data: InventoryItem[] }) => ({ ...context, eligibleItems: event.data }),
        setError: (context, event: { message: string | null }) => ({ ...context, error: event.message })
    }
});

export const inventoryActions = {
    async fetchItems(): Promise<void> {
        inventoryStore.trigger.setLoading({ value: true });
        inventoryStore.trigger.setError({ message: null });
        try {
            await businessEntityActions.fetchEntity();
            const inventoryId = businessEntityStore.getSnapshot().context.inventoryId;
            if (!inventoryId) throw new Error("Could not load inventory sub-entity ID");

            const res = await fetch(`${API_BASE}/values_with_comparison/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ref_business_entity: inventoryId })
            });
            const result = await res.json();

            const items: InventoryItem[] = [];
            if (result.value) {
                result.value.forEach((val: any) => {
                    const comp = result.comparison_value ? result.comparison_value.find((c: any) => c.value_from === val.id) : null;
                    items.push({
                        id: val.id,
                        uid: val.uid,
                        name: val.name,
                        type: val.type,
                        expression: val.expression,
                        identifier: val.identifier,
                        comparison_id: comp ? comp.id : null,
                        quantity_from: comp ? comp.quantity_from : 1,
                        quantity_to: comp ? comp.quantity_to : 0,
                        value_to: comp ? comp.value_to : null,
                        balance: 0,
                        ref_super_values_ids: val.ref_super_values_ids || [],
                        meta: val.meta || []
                    });
                });
            }
            inventoryStore.trigger.setItems({ data: items });
        } catch (error: any) {
            console.error("Failed to fetch inventory: ", error);
            inventoryStore.trigger.setError({ message: error.message || 'Unknown error' });
        } finally {
            inventoryStore.trigger.setLoading({ value: false });
        }
    },

    async fetchEligibleItems(): Promise<void> {
        try {
            await businessEntityActions.fetchEntity();
            const inventoryId = businessEntityStore.getSnapshot().context.inventoryId;
            if (!inventoryId) throw new Error("Inventory sub-entity ID not found for eligible items");

            const res = await fetch(`${API_BASE}/values_with_comparison/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ref_business_entity: inventoryId
                })
            });
            const result = await res.json();

            const eligibleItems: any[] = [];
            if (result.value) {
                const allowedTypes = ['ingredient', 'made-from', 'by-product'];
                result.value.forEach((val: any) => {
                    if (allowedTypes.includes(val.type)) {
                        eligibleItems.push({
                            id: val.id,
                            uid: val.uid,
                            name: val.name,
                            type: val.type,
                            expression: val.expression
                        });
                    }
                });
            }

            inventoryStore.trigger.setEligibleItems({ data: eligibleItems as InventoryItem[] });
        } catch (error) {
            console.error("Failed to fetch eligible items: ", error);
        }
    },

    async saveItem(editingItem: InventoryItem | null, formData: any): Promise<boolean> {
        try {
            const capitalize = (s: string) => (s && typeof s === 'string' ? s.charAt(0).toUpperCase() + s.slice(1) : s);

            await businessEntityActions.fetchEntity();
            const inventoryId = businessEntityStore.getSnapshot().context.inventoryId;
            if (!inventoryId) throw new Error("Inventory sub-entity ID not found for saving item");

            const body: any = {
                value: {
                    name: capitalize(formData.name),
                    expression: formData.expression,
                    type: formData.type,
                    ref_business_entity: inventoryId,
                    meta: []
                },
                comparison_value: {
                    quantity_from: 1,
                    quantity_to: parseFloat(formData.price) || 0,
                    value_to: formData.currency_id || null,
                    ref_business_entity: inventoryId
                },
                ref_super_values_ids: [],
                business_entity_ids: [inventoryId],
                balance_type: 'inventory'
            };

            if (formData.type === 'made-from' && formData.ingredients) {
                body.ref_super_values_ids = formData.ingredients.map((id: string) => parseInt(id));
            } else if (formData.type === 'by-product') {
                if (formData.source_id) {
                    body.ref_super_values_ids = [parseInt(formData.source_id)];
                }
                if (formData.value_ratio) {
                    body.value.meta.push({
                        key: 'value_ratio',
                        value: formData.value_ratio.toString()
                    });
                }
            }

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
        } catch (error: any) {
            console.error("Failed to save inventory item: ", error);
            inventoryStore.trigger.setError({ message: error.message || 'Failed to save item' });
            return false;
        }
    },

    async deleteItem(id: number, comparisonId?: number | null): Promise<boolean> {
        try {
            await fetch(`${API_BASE}/values/id/${id}`, { method: 'DELETE' });
            if (comparisonId) {
                await fetch(`${API_BASE}/comparison_values/id/${comparisonId}`, { method: 'DELETE' });
            }
            await this.fetchItems();
            return true;
        } catch (error: any) {
            console.error("Failed to delete inventory item: ", error);
            inventoryStore.trigger.setError({ message: error.message || 'Failed to delete item' });
            return false;
        }
    }
};
