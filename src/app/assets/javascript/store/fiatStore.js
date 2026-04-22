/**
 * @fileoverview Fiat Store Module.
 *
 * This module manages global currency data, exchange rates, and custom comparisons
 * using `@xstate/store`. It includes persistent storage in localStorage and
 * provides an Alpine.js data component for reactive UI binding.
 */

import { createStore } from '@xstate/store';

/**
 * @typedef {Object} Fiat
 * @property {number} id - Unique identifier for the currency.
 * @property {string} name - Human-readable name (e.g., "Dollar").
 * @property {string} expression - Cultural/symbolic representation (e.g., "USD" or "$").
 */

/**
 * @typedef {Object} Comparison
 * @property {number} id - Unique identifier for the comparison.
 * @property {number} value_from - Source currency ID.
 * @property {number} value_to - Target currency ID.
 * @property {number} quantity_from - Base quantity of the source currency.
 * @property {number} quantity_to - Resulting quantity of the target currency.
 * @property {string} context - The context of the comparison (e.g., "main", "custom").
 */

/**
 * @typedef {Object} StoreContext
 * @property {Fiat[]} fiats - List of all registered fiat currencies.
 * @property {number|null} mainFiatId - ID of the primary/main currency.
 * @property {Comparison[]} comparisons - List of all currency comparisons/rates.
 * @property {Object.<number, number>} exchangeRates - Derived rates mapped by target fiat ID.
 * @property {boolean} loading - Global loading state indicator.
 */

const PERSIST_KEY = 'fiat-store-persist';

/**
 * Loads the persisted store state from localStorage.
 * @returns {Partial<StoreContext>}
 */
const loadPersistedState = () => {
    try {
        return JSON.parse(localStorage.getItem(PERSIST_KEY) || '{}');
    } catch (e) {
        return {};
    }
};

const persistedState = loadPersistedState();

/**
 * The XState Store instance for Fiat management.
 */
export const fiatStore = createStore({
    context: {
        fiats: persistedState.fiats || [],
        mainFiatId: persistedState.mainFiatId || null,
        comparisons: persistedState.comparisons || [],
        exchangeRates: persistedState.exchangeRates || {},
        loading: false,
    },
    on: {
        setLoading: (context, event) => ({ ...context, loading: event.value }),
        setFiats: (context, event) => ({ ...context, fiats: event.data }),
        setMainFiat: (context, event) => ({ ...context, mainFiatId: event.id }),
        setComparisons: (context, event) => ({ ...context, comparisons: event.data }),
        setExchangeRates: (context, event) => ({ ...context, exchangeRates: event.rates })
    }
});

// Subscribe to state changes to persist the context
fiatStore.subscribe((snapshot) => {
    localStorage.setItem(PERSIST_KEY, JSON.stringify(snapshot.context));
});

const API_BASE = '/api/v1';

/**
 * Object containing all side-effect actions for the Fiat Store.
 */
export const fiatActions = {
    /**
     * Fetches all fiat currencies, comparisons, and settings from the backend.
     * Updates the store with the retrieved data and derives exchange rates.
     * @async
     * @returns {Promise<void>}
     */
    async fetchFiats() {
        fiatStore.trigger.setLoading({ value: true });
        try {
            const res = await fetch(`${API_BASE}/values/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: 'fiat', context: 'global', page_size: 100, balances: true })
            });
            const data = res.ok ? await res.json() : [];
            const fiatList = Array.isArray(data) ? data : (data && Array.isArray(data.data) ? data.data : []);
            fiatStore.trigger.setFiats({ data: fiatList });

            // Fetch Main and Custom comparisons
            const [mainRes, customRes] = await Promise.all([
                fetch(`${API_BASE}/comparison_values/?context=main`),
                fetch(`${API_BASE}/comparison_values/?context=custom`)
            ]);
            const mainComps = mainRes.ok ? (await mainRes.json()).data || [] : [];
            const customComps = customRes.ok ? (await customRes.json()).data || [] : [];
            /** @type {Comparison[]} */
            const comps = Array.isArray(mainComps) && Array.isArray(customComps) ? [...mainComps, ...customComps] : [];
            fiatStore.trigger.setComparisons({ data: comps });

            // Fetch main fiat option
            const optRes = await fetch(`${API_BASE}/options/?context=global`);
            const optData = await optRes.json();
            const mainOption = optData.find(o => o.name === 'main_fiat_currency');
            if (mainOption) {
                fiatStore.trigger.setMainFiat({ id: parseInt(mainOption.value) });
            }

            // Derive exchange rates based on main fiat
            const rates = {};
            const mainFiatId = fiatStore.getSnapshot().context.mainFiatId;
            if (comps && mainFiatId) {
                comps.forEach(comp => {
                    if (comp.context === 'main') {
                        if (comp.value_from === mainFiatId) {
                            rates[comp.value_to] = comp.quantity_to / comp.quantity_from;
                        } else if (comp.value_to === mainFiatId) {
                            rates[comp.value_from] = comp.quantity_from / comp.quantity_to;
                        }
                    }
                });
            }
            fiatStore.trigger.setExchangeRates({ rates });

        } catch (error) {
            console.error("Failed to fetch fiats: ", error);
        } finally {
            fiatStore.trigger.setLoading({ value: false });
        }
    },

    /**
     * Sets a currency as the main fiat currency.
     * @async
     * @param {number} id - The ID of the currency to set as main.
     * @returns {Promise<void>}
     */
    async setMainFiat(id) {
        try {
            const optRes = await fetch(`${API_BASE}/options/?context=global`);
            const optData = await optRes.json();
            const mainOption = optData.find(o => o.name === 'main_fiat_currency');

            if (mainOption) {
                await fetch(`${API_BASE}/options/id/${mainOption.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: 'main_fiat_currency', context: 'global', value: id.toString() })
                });
            } else {
                await fetch(`${API_BASE}/options/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: 'main_fiat_currency', context: 'global', value: id.toString() })
                });
            }
            fiatStore.trigger.setMainFiat({ id });
            await this.fetchFiats(); // Refresh rates to ensure consistency
        } catch (error) {
            console.error("Failed to set main fiat: ", error);
        }
    },

    /**
     * Creates a new fiat currency definition.
     * @async
     * @param {string} name - Name of the currency.
     * @param {string} expression - Symbol or code.
     * @returns {Promise<void>}
     */
    async createFiat(name, expression) {
        try {
            await fetch(`${API_BASE}/values/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, expression, type: 'fiat', context: 'global' })
            });
            await this.fetchFiats();
        } catch (error) {
            console.error("Failed to create fiat: ", error);
        }
    },

    /**
     * Creates or updates a comparison link between two currencies.
     * @async
     * @param {number} fromId - Source currency ID.
     * @param {number} toId - Target currency ID.
     * @param {number} rate - The exchange rate (1 source = X target).
     * @param {string} [context='main'] - Operation context.
     * @returns {Promise<void>}
     */
    async createLink(fromId, toId, rate, context = 'main') {
        try {
            const comps = fiatStore.getSnapshot().context.comparisons;
            const existing = comps.find(c => c.value_from === fromId && c.value_to === toId && c.context === context);

            const body = { quantity_from: 1, quantity_to: rate, value_from: fromId, value_to: toId, context };

            if (existing) {
                await fetch(`${API_BASE}/comparison_values/id/${existing.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });
            } else {
                await fetch(`${API_BASE}/comparison_values/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });
            }
            await this.fetchFiats();
        } catch (error) {
            console.error("Failed to create link: ", error);
        }
    },

    /**
     * Deletes a fiat currency definition.
     * @async
     * @param {number} id - ID of the currency to delete.
     * @returns {Promise<void>}
     */
    async deleteFiat(id) {
        try {
            await fetch(`${API_BASE}/values/id/${id}`, { method: 'DELETE' });
            await this.fetchFiats();
        } catch (error) {
            console.error("Failed to delete fiat: ", error);
        }
    },

    /**
     * Updates an existing custom comparison rate.
     * @async
     * @param {number} compId - Comparison ID.
     * @param {number} fromId - Source currency ID.
     * @param {number} toId - Target currency ID.
     * @param {number} rate - The exchange rate.
     * @param {string} [context='custom'] - Operation context.
     * @returns {Promise<void>}
     */
    async updateComparison(compId, fromId, toId, rate, context = 'custom') {
        try {
            await fetch(`${API_BASE}/comparison_values/id/${compId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ quantity_from: 1, quantity_to: rate, value_from: fromId, value_to: toId, context })
            });
            await this.fetchFiats();
        } catch (error) {
            console.error("Failed to update comparison: ", error);
        }
    },

    /**
     * Deletes a currency comparison definition.
     * @async
     * @param {number} id - ID of the comparison to delete.
     * @returns {Promise<void>}
     */
    async deleteComparison(id) {
        try {
            await fetch(`${API_BASE}/comparison_values/id/${id}`, { method: 'DELETE' });
            await this.fetchFiats();
        } catch (error) {
            console.error("Failed to delete comparison: ", error);
        }
    }
};
