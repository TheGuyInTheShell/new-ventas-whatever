import { createStore } from '@xstate/store';
import { BusinessEntityStoreContext } from '../types/business';
import { api } from '../lib/api';
import { RSBusinessEntitySearchChild } from '../types/api';

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
        setEntityId: (context: BusinessEntityStoreContext, event: { id: string | number | null }) => ({ ...context, entityId: event.id === 'null' ? null : (typeof event.id === 'string' ? parseInt(event.id) : event.id) }),
        setInventoryId: (context: BusinessEntityStoreContext, event: { id: string | number | null }) => ({ ...context, inventoryId: event.id === 'null' ? null : (typeof event.id === 'string' ? parseInt(event.id) : event.id) }),
        setLoading: (context: BusinessEntityStoreContext, event: { value: boolean }) => ({ ...context, loading: event.value }),
        setFetchingPromise: (context: BusinessEntityStoreContext, event: { promise: Promise<void> | null }) => ({ ...context, fetchingPromise: event.promise }),
        setError: (context: BusinessEntityStoreContext, event: { message: string | null }) => ({ ...context, error: event.message })
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
                const { data } = await api.post<RSBusinessEntitySearchChild>('/business_entities/search/child', {
                    name: ENTITY_NAME,
                    child_name: "inventory"
                });

                if (data && data.parent) {
                    const entity = data.parent;
                    businessEntityStore.trigger.setEntityId({ id: entity.id });

                    if (data.child && data.child.name === 'inventory') {
                        businessEntityStore.trigger.setInventoryId({ id: data.child.id });
                    }
                } else {
                    console.warn(`Business entity relationship not found for '${ENTITY_NAME}'.`);
                }
            } catch (error: unknown) {
                const msg = error instanceof Error ? error.message : 'Unknown error';
                console.error("Failed to fetch business entity: ", error);
                businessEntityStore.trigger.setError({ message: msg });
            } finally {
                businessEntityStore.trigger.setLoading({ value: false });
                businessEntityStore.trigger.setFetchingPromise({ promise: null });
            }
        })();

        businessEntityStore.trigger.setFetchingPromise({ promise });
        return promise;
    }
};
