import { createStore } from '@xstate/store';

const API_BASE = '/api/v1';
const GLOBAL_ENTITY_NAME = 'global';

export interface GlobalStoreContext {
    globalEntityId: number | null;
    loading: boolean;
    fetchingPromise: Promise<void> | null;
    error: string | null;
}

export const globalStore = createStore({
    context: {
        globalEntityId: null,
        loading: false,
        fetchingPromise: null,
        error: null
    } as GlobalStoreContext,
    on: {
        setGlobalEntityId: (context, event: { id: number | null }) => ({ ...context, globalEntityId: event.id }),
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
                const res = await fetch(`${API_BASE}/business_entities/search/name`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: GLOBAL_ENTITY_NAME })
                });
                
                if (!res.ok) throw new Error(`Failed to fetch global entity: ${res.statusText}`);
                
                const entity = await res.json();
                if (entity && entity.id) {
                    globalStore.trigger.setGlobalEntityId({ id: entity.id });
                } else {
                    console.warn(`Global business entity '${GLOBAL_ENTITY_NAME}' not found.`);
                }
            } catch (error: any) {
                console.error("Failed to fetch global business entity: ", error);
                globalStore.trigger.setError({ message: error.message });
            } finally {
                globalStore.trigger.setLoading({ value: false });
                globalStore.trigger.setFetchingPromise({ promise: null });
            }
        })();

        globalStore.trigger.setFetchingPromise({ promise });
        return promise;
    }
};
