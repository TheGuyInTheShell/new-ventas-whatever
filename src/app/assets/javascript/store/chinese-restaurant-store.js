import { createStore } from '@xstate/store';

const API_BASE = '/api/v1';
const ENTITY_NAME = 'chinese-restaurant';

/**
 * @typedef {Object} BusinessEntityStoreContext
 * @property {number|null} entityId - The ID of the business entity.
 * @property {boolean} loading - Loading state indicator.
 * @property {Promise<void>|null} fetchingPromise - Ongoing fetch promise to avoid concurrent requests.
 * @property {string|null} error - Error message if a request fails.
 */

/**
 * The XState Store instance for Business Entity management.
 * @type {import('@xstate/store').Store<BusinessEntityStoreContext>}
 */
export const businessEntityStore = createStore({
    context: {
        entityId: null,
        loading: false,
        fetchingPromise: null,
        error: null
    },
    on: {
        setEntityId: (context, event) => ({ ...context, entityId: event.id === 'null' ? null : event.id }),
        setLoading: (context, event) => ({ ...context, loading: event.value }),
        setFetchingPromise: (context, event) => ({ ...context, fetchingPromise: event.promise }),
        setError: (context, event) => ({ ...context, error: event.message })
    }
});

/**
 * Object containing all side-effect actions for the Business Entity Store.
 */
export const businessEntityActions = {
    /**
     * Fetches the business entity ID from the backend using the predefined ENTITY_NAME.
     * @async
     * @returns {Promise<void>}
     */
    async fetchEntity() {
        const snap = businessEntityStore.getSnapshot().context;
        if (snap.entityId) return;
        if (snap.fetchingPromise) return snap.fetchingPromise;

        const promise = (async () => {
            businessEntityStore.trigger.setLoading({ value: true });
            try {
                const res = await fetch(`${API_BASE}/business_entities_search_by/search`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: ENTITY_NAME })
                });
                const data = await res.json();
                if (data && data.data && data.data.length > 0) {
                    const entity = data.data.find(e => e.name === ENTITY_NAME) || data.data[0];
                    businessEntityStore.trigger.setEntityId({ id: entity.id });
                } else {
                    console.warn(`Business entity '${ENTITY_NAME}' not found.`);
                }
            } catch (error) {
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
