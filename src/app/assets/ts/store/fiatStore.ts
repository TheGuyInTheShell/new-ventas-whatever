import { createStore } from '@xstate/store';
import { businessEntityStore, businessEntityActions } from './chinese-restaurant-store';
import { Comparison, Fiat, FiatStoreContext } from '../types/fiat';

const PERSIST_KEY = 'fiat-store-persist';

const loadPersistedState = (): Partial<FiatStoreContext> => {
    try {
        return JSON.parse(localStorage.getItem(PERSIST_KEY) || '{}');
    } catch (e) {
        return {};
    }
};

const persistedState = loadPersistedState();

export const fiatStore = createStore({
    context: {
        fiats: persistedState.fiats || [],
        mainFiatId: persistedState.mainFiatId || null,
        comparisons: persistedState.comparisons || [],
        exchangeRates: persistedState.exchangeRates || {},
        loading: false,
    } as FiatStoreContext,
    on: {
        setLoading: (context, event: { value: boolean }) => ({ ...context, loading: event.value }),
        setFiats: (context, event: { data: Fiat[] }) => ({ ...context, fiats: event.data }),
        setMainFiat: (context, event: { id: number }) => ({ ...context, mainFiatId: event.id }),
        setComparisons: (context, event: { data: Comparison[] }) => ({ ...context, comparisons: event.data }),
        setExchangeRates: (context, event: { rates: Record<number, number> }) => ({ ...context, exchangeRates: event.rates })
    }
});

fiatStore.subscribe((snapshot) => {
    localStorage.setItem(PERSIST_KEY, JSON.stringify(snapshot.context));
});

const API_BASE = '/api/v1';

export const fiatActions = {
    async fetchFiats(): Promise<void> {
        fiatStore.trigger.setLoading({ value: true });
        try {
            await businessEntityActions.fetchEntity();
            const entityId = businessEntityStore.getSnapshot().context.entityId;
            if (!entityId) throw new Error("Business entity 'chinese-restaurant' ID not found");

            const res = await fetch(`${API_BASE}/values/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    type: 'fiat',
                    page_size: 100,
                    balances: true,
                    ref_business_entity: entityId
                })
            });
            const data = res.ok ? await res.json() : [];
            const fiatList = Array.isArray(data) ? data : (data && Array.isArray(data.data) ? data.data : []);
            fiatStore.trigger.setFiats({ data: fiatList });

            const compsRes = await fetch(`${API_BASE}/comparison_values/?ref_business_entity=${entityId}`);
            const compsData = compsRes.ok ? (await compsRes.json()).data || [] : [];
            const comps: Comparison[] = Array.isArray(compsData) ? compsData : [];
            fiatStore.trigger.setComparisons({ data: comps });

            const optRes = await fetch(`${API_BASE}/options/?context=global`);
            const optData = await optRes.json();
            const mainOption = optData.find((o: any) => o.name === 'main_fiat_currency');
            if (mainOption) {
                fiatStore.trigger.setMainFiat({ id: parseInt(mainOption.value) });
            }

            const rates: Record<number, number> = {};
            const mainFiatId = fiatStore.getSnapshot().context.mainFiatId;
            if (comps && mainFiatId) {
                comps.forEach(comp => {
                    if (Number(comp.value_from) === Number(mainFiatId) || Number(comp.value_to) === Number(mainFiatId)) {
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

    async setMainFiat(id: number): Promise<void> {
        try {
            const optRes = await fetch(`${API_BASE}/options/?context=global`);
            const optData = await optRes.json();
            const mainOption = optData.find((o: any) => o.name === 'main_fiat_currency');

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
            await this.fetchFiats();
        } catch (error) {
            console.error("Failed to set main fiat: ", error);
        }
    },

    async createFiat(name: string, expression: string): Promise<void> {
        try {
            await businessEntityActions.fetchEntity();
            const entityId = businessEntityStore.getSnapshot().context.entityId;
            if (!entityId) throw new Error("Business entity ID required to create fiat");

            await fetch(`${API_BASE}/values/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name,
                    expression,
                    type: 'fiat',
                    ref_business_entity: entityId
                })
            });
            await this.fetchFiats();
        } catch (error) {
            console.error("Failed to create fiat: ", error);
        }
    },

    async createLink(fromId: number, toId: number, rate: number): Promise<void> {
        try {
            // Ensure data is fresh before checking for existing links
            await this.fetchFiats();
            
            await businessEntityActions.fetchEntity();
            const entityId = businessEntityStore.getSnapshot().context.entityId;
            if (!entityId) throw new Error("Business entity ID required to create link");

            const comps = fiatStore.getSnapshot().context.comparisons;
            const existing = comps.find(c => Number(c.value_from) === Number(fromId) && Number(c.value_to) === Number(toId));

            const body = {
                quantity_from: 1,
                quantity_to: rate,
                value_from: fromId,
                value_to: toId,
                ref_business_entity: entityId
            };

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

    async deleteFiat(id: number): Promise<void> {
        try {
            await fetch(`${API_BASE}/values/id/${id}`, { method: 'DELETE' });
            await this.fetchFiats();
        } catch (error) {
            console.error("Failed to delete fiat: ", error);
        }
    },

    async updateComparison(compId: number, fromId: number, toId: number, rate: number): Promise<void> {
        try {
            await businessEntityActions.fetchEntity();
            const entityId = businessEntityStore.getSnapshot().context.entityId;
            if (!entityId) throw new Error("Business entity ID required to update comparison");

            await fetch(`${API_BASE}/comparison_values/id/${compId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    quantity_from: 1,
                    quantity_to: rate,
                    value_from: fromId,
                    value_to: toId,
                    ref_business_entity: entityId
                })
            });
            await this.fetchFiats();
        } catch (error) {
            console.error("Failed to update comparison: ", error);
        }
    },

    async deleteComparison(id: number): Promise<void> {
        try {
            await fetch(`${API_BASE}/comparison_values/id/${id}`, { method: 'DELETE' });
            await this.fetchFiats();
        } catch (error) {
            console.error("Failed to delete comparison: ", error);
        }
    }
};
