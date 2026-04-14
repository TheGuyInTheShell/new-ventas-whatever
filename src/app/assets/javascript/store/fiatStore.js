import { createStore } from '@xstate/store';

// We load the persisted store config if available
const PERSIST_KEY = 'fiat-store-persist';
const persistedState = JSON.parse(localStorage.getItem(PERSIST_KEY) || '{}');

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

// Persist the state whenever it changes
fiatStore.subscribe((snapshot) => {
    localStorage.setItem(PERSIST_KEY, JSON.stringify(snapshot.context));
});

// Define Actions connected to the store
const API_BASE = '/api/v1'; // Assuming default API base, standard to fastAPI setups

export const fiatActions = {
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
            const comps = [...mainComps, ...customComps];
            fiatStore.trigger.setComparisons({ data: comps });

            // Fetch main fiat
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
            await this.fetchFiats(); // Refresh rates
        } catch (error) {
            console.error("Failed to set main fiat: ", error);
        }
    },

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

    async createLink(fromId, toId, rate, context = 'main') {
        try {
            const comps = fiatStore.getSnapshot().context.comparisons;
            const existing = comps.find(c => c.value_from === fromId && c.value_to === toId && c.context === context);

            if (existing) {
                await fetch(`${API_BASE}/comparison_values/id/${existing.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ quantity_from: 1, quantity_to: rate, value_from: fromId, value_to: toId, context })
                });
            } else {
                await fetch(`${API_BASE}/comparison_values/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ quantity_from: 1, quantity_to: rate, value_from: fromId, value_to: toId, context })
                });
            }
            await this.fetchFiats();
        } catch (error) {
            console.error("Failed to create link: ", error);
        }
    },

    async deleteFiat(id) {
        try {
            await fetch(`${API_BASE}/values/id/${id}`, { method: 'DELETE' });
            await this.fetchFiats();
        } catch (error) {
            console.error("Failed to delete fiat: ", error);
        }
    },

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

    async deleteComparison(id) {
        try {
            await fetch(`${API_BASE}/comparison_values/id/${id}`, { method: 'DELETE' });
            await this.fetchFiats();
        } catch (error) {
            console.error("Failed to delete comparison: ", error);
        }
    }
};

// Bind to Alpine context
document.addEventListener('alpine:init', () => {
    Alpine.data('fiatConfig', () => ({
        storeContext: fiatStore.getSnapshot().context,
        newFiat: { name: '', expression: '' },
        newComparison: { fromId: null, toId: null, rate: null },
        compRates: {},
        isAddingFiat: false,

        init() {
            // Subscribe to store updates
            fiatStore.subscribe(snapshot => {
                this.storeContext = snapshot.context;
            });

            fiatActions.fetchFiats();
        },

        get fiats() { return this.storeContext.fiats; },
        get mainFiatId() { return this.storeContext.mainFiatId; },
        get comparisons() { return this.storeContext.comparisons; },
        get exchangeRates() { return this.storeContext.exchangeRates; },
        get customComparisons() { return this.storeContext.comparisons.filter(c => c.context === 'custom'); },

        async onAddFiat() {
            if (this.newFiat.name && this.newFiat.expression) {
                this.isAddingFiat = true;
                await fiatActions.createFiat(this.newFiat.name, this.newFiat.expression);
                this.newFiat.name = '';
                this.newFiat.expression = '';
                this.isAddingFiat = false;
            }
        },

        async onSetMainFiat(id) {
            await fiatActions.setMainFiat(id);
        },

        async onSetRate(fiatId, rate) {
            if (this.mainFiatId && rate) {
                await fiatActions.createLink(this.mainFiatId, fiatId, parseFloat(rate), 'main');
            }
        },

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

        async onDeleteFiat(id) {
            if(confirm('Are you sure you want to delete this currency?')) {
                await fiatActions.deleteFiat(id);
            }
        },

        async onDeleteComparison(id) {
            if(confirm('Are you sure you want to delete this comparison?')) {
                await fiatActions.deleteComparison(id);
            }
        },

        getFiatName(id) {
            const f = this.fiats.find(f => f.id === id);
            return f ? f.name : `#${id}`;
        },

        getFiatExpression(id) {
            const f = this.fiats.find(f => f.id === id);
            return f ? f.expression : '';
        }

    }));
});
