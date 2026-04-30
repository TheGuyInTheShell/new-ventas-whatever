import { createStore } from '@xstate/store';
import { BusinessEntityStoreContext } from '../types/business';

const API_BASE = '/api/v1';
const ENTITY_NAME = 'chinese-restaurant';

export const businessEntityStore = createStore({
    context: {
        entityId: null,
        inventoryId: null,
        loading: false,
        fetchingPromise: null,
        error: null
    } as BusinessEntityStoreContext,
    on: {
        setEntityId: (context, event: { id: string | number | null }) => ({ ...context, entityId: event.id === 'null' ? null : (typeof event.id === 'string' ? parseInt(event.id) : event.id) }),
        setInventoryId: (context, event: { id: string | number | null }) => ({ ...context, inventoryId: event.id === 'null' ? null : (typeof event.id === 'string' ? parseInt(event.id) : event.id) }),
        setLoading: (context, event: { value: boolean }) => ({ ...context, loading: event.value }),
        setFetchingPromise: (context, event: { promise: Promise<void> | null }) => ({ ...context, fetchingPromise: event.promise }),
        setError: (context, event: { message: string | null }) => ({ ...context, error: event.message })
    }
});

export const businessEntityActions = {
    async fetchEntity(): Promise<void> {
        const snap = businessEntityStore.getSnapshot().context;
        if (snap.entityId) return;
        if (snap.fetchingPromise) return snap.fetchingPromise;

        const promise = (async () => {
            businessEntityStore.trigger.setLoading({ value: true });
            try {
                const res = await fetch(`${API_BASE}/business_entities/search/child`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: ENTITY_NAME, child_name: "inventory" })
                });
                const data = await res.json();
                
                if (data && data.parent) {
                    const entity = data.parent;
                    businessEntityStore.trigger.setEntityId({ id: entity.id });
                    
                    if (data.child && data.child.name === 'inventory') {
                        businessEntityStore.trigger.setInventoryId({ id: data.child.id });
                    }
                } else {
                    console.warn(`Business entity relationship not found for '${ENTITY_NAME}'.`);
                }
            } catch (error: any) {
                console.error("Failed to fetch business entity: ", error);
                businessEntityStore.trigger.setError({ message: error.message });
            } finally {
                businessEntityStore.trigger.setLoading({ value: false });
                businessEntityStore.trigger.setFetchingPromise({ promise: null });
            }
        })();

        businessEntityStore.trigger.setFetchingPromise({ promise });
        return promise;
    }
};
