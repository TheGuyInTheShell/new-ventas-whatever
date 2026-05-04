import { createStore } from '@xstate/store';
import { globalStore, globalActions } from './global-store';
import { Comparison, Fiat, FiatStoreContext } from '../types/fiat';
import { api } from '../lib/api';
import { RSValue, RSComparisonValue } from '../types/api';

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
        setLoading: (context: FiatStoreContext, event: { value: boolean }) => ({ ...context, loading: event.value }),
        setFiats: (context: FiatStoreContext, event: { data: Fiat[] }) => ({ ...context, fiats: event.data }),
        setMainFiat: (context: FiatStoreContext, event: { id: number }) => ({ ...context, mainFiatId: event.id }),
        setComparisons: (context: FiatStoreContext, event: { data: Comparison[] }) => ({ ...context, comparisons: event.data }),
        setExchangeRates: (context: FiatStoreContext, event: { rates: Record<number, number> }) => ({ ...context, exchangeRates: event.rates })
    }
});

fiatStore.subscribe((snapshot: any) => {
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

            const { data: result } = await api.post<any>('/values/query', {
                type: 'fiat',
                page_size: 100,
                balances: true,
                ref_business_entity: baseEntityId
            });
            const fiatList = Array.isArray(result) ? result : (result && Array.isArray(result.data) ? result.data : []);
            fiatStore.trigger.setFiats({ data: fiatList });

            // Fetch comparisons for both current and custom if they exist
            const fetchComps = async (id: number): Promise<RSComparisonValue[]> => {
                const { data } = await api.get<any>(`/comparison_values/?ref_business_entity=${id}`);
                return data.data || [];
            };

            const [currentComps, customComps] = await Promise.all([
                currentId ? fetchComps(currentId).then(list => list.map((c: any) => ({ ...c, context: 'current' }))) : Promise.resolve([]),
                customId ? fetchComps(customId).then(list => list.map((c: any) => ({ ...c, context: 'custom' }))) : Promise.resolve([])
            ]);

            const comps: Comparison[] = [...currentComps, ...customComps];
            fiatStore.trigger.setComparisons({ data: comps });

            const { data: optData } = await api.get<any[]>('/options/?context=global');
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
            const { data: optData } = await api.get<any[]>('/options/?context=global');
            const mainOption = optData.find((o: any) => o.name === 'main_fiat_currency');

            if (mainOption) {
                await api.put(`/options/id/${mainOption.id}`, {
                    name: 'main_fiat_currency',
                    context: 'global',
                    value: id.toString()
                });
            } else {
                await api.post('/options/', {
                    name: 'main_fiat_currency',
                    context: 'global',
                    value: id.toString()
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

            await api.post('/values/', {
                name,
                expression,
                type: 'fiat',
                ref_business_entity: entityId
            });
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

            if (existing) {
                await api.put(`/comparison_values/id/${existing.id}`, body);
            } else {
                await api.post('/comparison_values/', body);
            }
            await this.fetchFiats();
            return true;
        } catch (error) {
            console.error("Failed to create link: ", error);
            throw error;
        }
    },

    async deleteFiat(id: number): Promise<boolean> {
        try {
            await api.delete(`/values/id/${id}`);
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

            await api.put(`/comparison_values/id/${compId}`, {
                quantity_from: 1,
                quantity_to: rate,
                value_from: fromId,
                value_to: toId,
                ref_business_entity: entityId
            });
            await this.fetchFiats();
        } catch (error) {
            console.error("Failed to update comparison: ", error);
        }
    },

    async deleteComparison(id: number): Promise<boolean> {
        try {
            await api.delete(`/comparison_values/id/${id}`);
            await this.fetchFiats();
            return true;
        } catch (error) {
            console.error("Failed to delete comparison: ", error);
            throw error;
        }
    }
};
