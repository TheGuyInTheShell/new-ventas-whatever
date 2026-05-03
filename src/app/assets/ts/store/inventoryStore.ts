import { createStore } from '@xstate/store';
import { InventoryItem, InventoryStoreContext } from '../types/inventory';
import { businessEntityStore, businessEntityActions } from './chinese-restaurant-store';

const API_BASE = '/api/v1';

export const inventoryStore = createStore({
    context: {
        items: [],
        eligibleItems: [],
        loading: false,
        error: null
    } as InventoryStoreContext,
    on: {
        setLoading: (context, event: { value: boolean }) => ({ ...context, loading: event.value }),
        setItems: (context, event: { data: InventoryItem[] }) => ({ ...context, items: event.data }),
        setEligibleItems: (context, event: { data: InventoryItem[] }) => ({ ...context, eligibleItems: event.data }),
        setError: (context, event: { message: string | null }) => ({ ...context, error: event.message })
    }
});

export const inventoryActions = {
    async fetchItems() {
        inventoryStore.trigger.setLoading({ value: true });
        try {
            await businessEntityActions.fetchEntity();
            const inventoryId = businessEntityStore.getSnapshot().context.inventoryId;

            const res = await fetch(`${API_BASE}/values_with_comparison/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    ref_business_entity: inventoryId,
                    value: {
                        full_meta: true
                    }
                })
            });
            const result = await res.json();
            console.log("Inventory API Result:", result);
            
            const items: InventoryItem[] = [];
            if (result.value) {
                const allowedTypes = ['ingredient', 'made-from', 'by-product'];
                result.value.forEach((val: any) => {
                    if (allowedTypes.includes(val.type)) {
                        const comps = result.comparison_value ? result.comparison_value.filter((c: any) => c.value_from === val.id) : [];
                        const primaryComp = comps.length > 0 ? comps[0] : null;

                        const primaryBalance = (val.balances && val.balances.length > 0) ? val.balances[0] : null;
                        
                        items.push({
                            id: val.id,
                            uid: val.uid,
                            name: val.name,
                            type: val.type,
                            expression: val.expression,
                            identifier: val.identifier,
                            comparison_id: primaryComp ? primaryComp.id : null,
                            quantity_from: primaryComp ? primaryComp.quantity_from : 1,
                            quantity_to: primaryComp ? primaryComp.quantity_to : 0,
                            value_to: primaryComp ? primaryComp.value_to : null,
                            balance: primaryBalance ? primaryBalance.quantity : 0,
                            balance_id: primaryBalance ? primaryBalance.id : undefined,
                            ref_super_values_ids: val.ref_super_values_ids || [],
                            meta: val.meta || [],
                            prices: comps.map((c: any) => ({
                                comparison_id: c.id,
                                quantity_to: c.quantity_to,
                                quantity_from: c.quantity_from,
                                fiat_id: c.value_to
                            }))
                        });
                    }
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

    async adjustStock(item: InventoryItem, newQuantity: number, isAdjustment: boolean, notes: string): Promise<boolean> {
        try {
            await businessEntityActions.fetchEntity();
            const inventoryId = businessEntityStore.getSnapshot().context.inventoryId;

            const payload = {
                balance_id: item.balance_id || null,
                value_id: item.id,
                ref_business_entity: inventoryId,
                new_quantity: newQuantity,
                is_adjustment: isAdjustment,
                notes: notes
            };

            const res = await fetch(`${API_BASE}/transaction_and_invoice/adjust`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error('Failed to adjust stock');

            await this.fetchItems();
            return true;
        } catch (error: any) {
            console.error("Failed to adjust stock: ", error);
            inventoryStore.trigger.setError({ message: error.message || 'Failed to adjust stock' });
            return false;
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
                    ref_business_entity: inventoryId,
                    value: {
                        full_meta: true
                    }
                })
            });
            const result = await res.json();
            const items: any[] = [];
            if (result.value) {
                result.value.forEach((val: any) => {
                    items.push({
                        id: val.id,
                        name: val.name,
                        expression: val.expression
                    });
                });
            }
            inventoryStore.trigger.setEligibleItems({ data: items });
        } catch (error: any) {
            console.error("Failed to fetch eligible items: ", error);
        }
    },

    async saveItem(itemData: Partial<InventoryItem>): Promise<boolean> {
        try {
            await businessEntityActions.fetchEntity();
            const inventoryId = businessEntityStore.getSnapshot().context.inventoryId;
            if (!inventoryId) throw new Error("Inventory sub-entity ID not found for saving items");

            const payload = {
                value: {
                    name: itemData.name,
                    expression: itemData.expression,
                    type: itemData.type || 'ingredient',
                    ref_business_entity: inventoryId,
                    identifier: itemData.identifier,
                    price: itemData.quantity_to,
                    currency_id: itemData.value_to
                },
                comparison_value: {
                    quantity_from: itemData.quantity_from || 1,
                    quantity_to: itemData.quantity_to || 0,
                    value_to: itemData.value_to,
                    ref_business_entity: inventoryId
                },
                ref_super_values_ids: itemData.ref_super_values_ids || [],
                business_entity_ids: [inventoryId],
                balance_type: 'inventory'
            };

            const method = itemData.id ? 'PUT' : 'POST';
            const url = itemData.id ? `${API_BASE}/values_with_comparison/id/${itemData.uid}` : `${API_BASE}/values_with_comparison`;

            const res = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error('Failed to save inventory item');

            await this.fetchItems();
            return true;
        } catch (error: any) {
            console.error("Failed to save inventory item: ", error);
            inventoryStore.trigger.setError({ message: error.message || 'Failed to save item' });
            return false;
        }
    },

    async deleteItem(item: InventoryItem): Promise<boolean> {
        try {
            const res = await fetch(`${API_BASE}/values/id/${item.uid}`, {
                method: 'DELETE'
            });

            if (!res.ok) throw new Error('Failed to delete item');

            await this.fetchItems();
            return true;
        } catch (error: any) {
            console.error("Failed to delete inventory item: ", error);
            inventoryStore.trigger.setError({ message: error.message || 'Failed to delete item' });
            return false;
        }
    }
};
