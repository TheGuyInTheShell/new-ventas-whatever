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
            const data = await res.json();
            fiatStore.trigger.setFiats({ data: data || [] });

            // Fetch Main and Custom comparisons
            const [mainRes, customRes] = await Promise.all([
                fetch(`${API_BASE}/comparison_values/?context=main`),
                fetch(`${API_BASE}/comparison_values/?context=custom`)
            ]);
            const mainComps = (await mainRes.json()).data || [];
            const customComps = (await customRes.json()).data || [];
            /** @type {Comparison[]} */
            const comps = [...mainComps, ...customComps];
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

/**
 * Registers the 'fiatConfig' Alpine.js data component.
 * This component acts as a bridge between the reactive UI and the Fiat Store.
 */
document.addEventListener('alpine:init', () => {
    Alpine.data('fiatConfig', () => ({
        /** Current context snapshot from the fiatStore */
        storeContext: fiatStore.getSnapshot().context,
        /** Form state for creating a new fiat */
        newFiat: { name: '', expression: '' },
        /** Form state for creating a new comparison */
        newComparison: { fromId: null, toId: null, rate: null },
        /** Local UI state for comparison rates */
        compRates: {},
        /** Local UI state for add operation status */
        isAddingFiat: false,

        /**
         * Initializes the component. Subscribes to store changes and performs initial fetch.
         */
        init() {
            fiatStore.subscribe(snapshot => {
                this.storeContext = snapshot.context;
            });
            fiatActions.fetchFiats();
        },

        // Helper Getters
        get fiats() { return this.storeContext.fiats; },
        get mainFiatId() { return this.storeContext.mainFiatId; },
        get comparisons() { return this.storeContext.comparisons; },
        get exchangeRates() { return this.storeContext.exchangeRates; },
        /** Returns comparisons defined with 'custom' context */
        get customComparisons() { return this.storeContext.comparisons.filter(c => c.context === 'custom'); },

        /**
         * Event handler for adding a new fiat currency.
         * @async
         */
        async onAddFiat() {
            if (this.newFiat.name && this.newFiat.expression) {
                this.isAddingFiat = true;
                await fiatActions.createFiat(this.newFiat.name, this.newFiat.expression);
                this.newFiat.name = '';
                this.newFiat.expression = '';
                this.isAddingFiat = false;
            }
        },

        /**
         * Event handler for setting the main fiat currency.
         * @async
         * @param {number} id
         */
        async onSetMainFiat(id) {
            await fiatActions.setMainFiat(id);
        },

        /**
         * Event handler for updating an exchange rate between the main currency and another.
         * @async
         * @param {number} fiatId - The ID of the non-main fiat currency.
         * @param {string|number} rate - The exchange rate value.
         */
        async onSetRate(fiatId, rate) {
            if (this.mainFiatId && rate) {
                await fiatActions.createLink(this.mainFiatId, fiatId, parseFloat(rate), 'main');
            }
        },

        /**
         * Event handler for adding a custom comparison between any two currencies.
         * @async
         */
        async onAddComparison() {
            if (this.newComparison.fromId && this.newComparison.toId && this.newComparison.rate) {
                if (this.newComparison.fromId === this.newComparison.toId) {
                    alert('Cannot compare a currency with itself');
                    return;
                }
                await fiatActions.createLink(
                    parseInt(this.newComparison.fromId),
                    parseInt(this.newComparison.toId),
                    parseFloat(this.newComparison.rate),
                    'custom'
                );
                this.newComparison = { fromId: null, toId: null, rate: null };
            }
        },

        /**
         * Event handler for deleting a fiat currency.
         * @async
         * @param {number} id
         */
        async onDeleteFiat(id) {
            if(confirm('Are you sure you want to delete this currency?')) {
                await fiatActions.deleteFiat(id);
            }
        },

        /**
         * Event handler for deleting a custom comparison.
         * @async
         * @param {number} id
         */
        async onDeleteComparison(id) {
            if(confirm('Are you sure you want to delete this comparison?')) {
                await fiatActions.deleteComparison(id);
            }
        },

        /**
         * Returns the name of a currency given its ID.
         * @param {number} id
         * @returns {string}
         */
        getFiatName(id) {
            const f = this.fiats.find(f => f.id === id);
            return f ? f.name : `#${id}`;
        },

        /**
         * Returns the expression/symbol of a currency given its ID.
         * @param {number} id
         * @returns {string}
         */
        getFiatExpression(id) {
            const f = this.fiats.find(f => f.id === id);
            return f ? f.expression : '';
        }
    }));
});
