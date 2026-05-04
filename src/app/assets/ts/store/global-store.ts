import { createStore } from '@xstate/store';
import { api } from '../lib/api';
import { RSBusinessEntity, RSBusinessEntitySearchChild } from '../types/api';

const API_BASE = '/api/v1';
const GLOBAL_ENTITY_NAME = 'global';

export interface GlobalStoreContext {
    globalEntityId: number | null;
    entities: Record<string, number | null>;
    loading: boolean;
    fetchingPromise: Promise<void> | null;
    error: string | null;
}

export const globalStore = createStore({
    context: {
        globalEntityId: null,
        entities: {},
        loading: false,
        fetchingPromise: null,
        error: null
    } as GlobalStoreContext,
    on: {
        setGlobalEntityId: (context, event: { id: number | null }) => ({ ...context, globalEntityId: event.id }),
        setEntityId: (context, event: { name: string, id: number | null }) => ({ 
            ...context, 
            entities: { ...context.entities, [event.name]: event.id } 
        }),
        setLoading: (context, event: { value: boolean }) => ({ ...context, loading: event.value }),
        setFetchingPromise: (context, event: { promise: Promise<void> | null }) => ({ ...context, fetchingPromise: event.promise }),
        setError: (context, event: { message: string | null }) => ({ ...context, error: event.message })
    }
});

export const globalActions = {
    async fetchGlobalEntity(): Promise<void> {
        const snap = globalStore.getSnapshot().context;
        if (snap.globalEntityId) return;
        if (snap.fetchingPromise) return snap.fetchingPromise;

        const promise = (async () => {
            globalStore.trigger.setLoading({ value: true });
            try {
                const { data: entity } = await api.post<RSBusinessEntity>('/business_entities/search', {
                    name: GLOBAL_ENTITY_NAME,
                    hierarchy: true
                });
                if (entity && entity.id) {
                    console.log(`[GlobalStore] Global entity found with hierarchy:`, entity);
                    globalStore.trigger.setGlobalEntityId({ id: entity.id });
                    
                    // Recursively process hierarchy to fill the entities map
                    const processHierarchy = (item: RSBusinessEntity) => {
                        if (item.name) {
                            globalStore.trigger.setEntityId({ name: item.name, id: item.id });
                        }
                        if (item.children && Array.isArray(item.children)) {
                            item.children.forEach(processHierarchy);
                        }
                    };
                    processHierarchy(entity);
                    console.log(`[GlobalStore] Entities map populated:`, globalStore.getSnapshot().context.entities);
                } else {
                    console.warn(`[GlobalStore] Global business entity '${GLOBAL_ENTITY_NAME}' not found in response:`, entity);
                }
            } catch (error: unknown) {
                const msg = error instanceof Error ? error.message : 'Unknown error';
                console.error("Failed to fetch global business entity: ", error);
                globalStore.trigger.setError({ message: msg });
            } finally {
                globalStore.trigger.setLoading({ value: false });
                globalStore.trigger.setFetchingPromise({ promise: null });
            }
        })();

        globalStore.trigger.setFetchingPromise({ promise });
        return promise;
    },

    async fetchEntityByChild(parentName: string, childName: string): Promise<number | null> {
        try {
            const { data } = await api.post<RSBusinessEntitySearchChild>('/business_entities/search/child', {
                name: parentName,
                child_name: childName
            });
            if (data && data.child && data.child.id) {
                globalStore.trigger.setEntityId({ name: childName, id: data.child.id });
                return data.child.id;
            }
            return null;
        } catch (error) {
            console.error(`Failed to fetch child entity ${childName} of ${parentName}:`, error);
            return null;
        }
    },

    async fetchFinanceHierarchy(): Promise<void> {
        console.log("[GlobalStore] Starting finance hierarchy fetch (Optimized)...");
        // Ensure global and all its children (hierarchy) are fetched in one go
        await this.fetchGlobalEntity();
        console.log("[GlobalStore] Hierarchy fetch complete.", globalStore.getSnapshot().context.entities);
    }
};
