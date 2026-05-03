import { createStore } from '@xstate/store';
import { globalStore, globalActions } from './global-store';
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
            await globalActions.fetchFinanceHierarchy();
            const snap = globalStore.getSnapshot().context;
            console.log("[FiatStore] Snapshot before check:", snap);
            const globalId = snap.globalEntityId;
            const currentId = snap.entities['current'];
            const customId = snap.entities['custom'];

            if (!globalId) {
                console.error("[FiatStore] Global ID missing. Context entities:", snap.entities);
                throw new Error("Global business entity ID not found");
            }
            
            console.log(`[FiatStore] Using globalId: ${globalId}, currentId: ${currentId}, customId: ${customId}`);

            // Fetch fiats (usually from current or global)
            const baseEntityId = currentId || globalId;

            const res = await fetch(`${API_BASE}/values/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    type: 'fiat',
                    page_size: 100,
                    balances: true,
                    ref_business_entity: baseEntityId
                })
            });
            const data = res.ok ? await res.json() : [];
            const fiatList = Array.isArray(data) ? data : (data && Array.isArray(data.data) ? data.data : []);
            fiatStore.trigger.setFiats({ data: fiatList });

            // Fetch comparisons for both current and custom if they exist
            const fetchComps = async (id: number) => {
                const r = await fetch(`${API_BASE}/comparison_values/?ref_business_entity=${id}`);
                return r.ok ? (await r.json()).data || [] : [];
            };

            const [currentComps, customComps] = await Promise.all([
                currentId ? fetchComps(currentId).then(list => list.map((c: any) => ({ ...c, context: 'current' }))) : Promise.resolve([]),
                customId ? fetchComps(customId).then(list => list.map((c: any) => ({ ...c, context: 'custom' }))) : Promise.resolve([])
            ]);

            const comps: Comparison[] = [...currentComps, ...customComps];
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

            console.log("[FiatStore] Successfully fetched fiats and comparisons.", {
                fiats: fiatList.length,
                comparisons: comps.length
            });

        } catch (error) {
            console.error("[FiatStore] Failed to fetch fiats: ", error);
        } finally {
            fiatStore.trigger.setLoading({ value: false });
        }
    },

    async setMainFiat(id: number): Promise<boolean> {
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
            return true;
        } catch (error) {
            console.error("Failed to set main fiat: ", error);
            return false;
        }
    },

    async createFiat(name: string, expression: string): Promise<boolean> {
        try {
            await globalActions.fetchGlobalEntity();
            const entityId = globalStore.getSnapshot().context.globalEntityId;
            if (!entityId) throw new Error("Global business entity ID required to create fiat");

            const res = await fetch(`${API_BASE}/values/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name,
                    expression,
                    type: 'fiat',
                    ref_business_entity: entityId
                })
            });
            if (!res.ok) throw new Error("Server error creating currency");
            await this.fetchFiats();
            return true;
        } catch (error) {
            console.error("Failed to create fiat: ", error);
            throw error;
        }
    },

    async createLink(fromId: number, toId: number, rate: number, useCustom: boolean = false): Promise<boolean> {
        try {
            // Ensure data is fresh
            await this.fetchFiats();

            const snap = globalStore.getSnapshot().context;
            const targetEntityId = useCustom ? snap.entities['custom'] : snap.entities['current'];

            if (!targetEntityId) throw new Error(`Target business entity ID (${useCustom ? 'custom' : 'current'}) required to create link`);

            const comps = fiatStore.getSnapshot().context.comparisons;
            const existing = comps.find(c => Number(c.value_from) === Number(fromId) && Number(c.value_to) === Number(toId) && Number(c.ref_business_entity) === Number(targetEntityId));

            const body = {
                quantity_from: 1,
                quantity_to: rate,
                value_from: fromId,
                value_to: toId,
                ref_business_entity: targetEntityId
            };

            let res;
            if (existing) {
                res = await fetch(`${API_BASE}/comparison_values/id/${existing.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });
            } else {
                res = await fetch(`${API_BASE}/comparison_values/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });
            }
            if (!res.ok) throw new Error("Server error creating exchange rate");
            await this.fetchFiats();
            return true;
        } catch (error) {
            console.error("Failed to create link: ", error);
            throw error;
        }
    },

    async deleteFiat(id: number): Promise<boolean> {
        try {
            const res = await fetch(`${API_BASE}/values/id/${id}`, { method: 'DELETE' });
            if (!res.ok) throw new Error("Server error deleting currency");
            await this.fetchFiats();
            return true;
        } catch (error) {
            console.error("Failed to delete fiat: ", error);
            throw error;
        }
    },

    async updateComparison(compId: number, fromId: number, toId: number, rate: number): Promise<void> {
        try {
            await globalActions.fetchGlobalEntity();
            const entityId = globalStore.getSnapshot().context.globalEntityId;
            if (!entityId) throw new Error("Global business entity ID required to update comparison");

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

    async deleteComparison(id: number): Promise<boolean> {
        try {
            const res = await fetch(`${API_BASE}/comparison_values/id/${id}`, { method: 'DELETE' });
            if (!res.ok) throw new Error("Server error deleting comparison");
            await this.fetchFiats();
            return true;
        } catch (error) {
            console.error("Failed to delete comparison: ", error);
            throw error;
        }
    }
};
