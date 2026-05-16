import { createStore } from '@xstate/store';
import { globalStore, globalActions } from './global-store';
import { Comparison, Fiat, FiatStoreContext } from '../types/fiat';
import { api } from '../lib/api';
import { RSComparisonValue, RSOption } from '../types/api';

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

fiatStore.subscribe((snapshot: { context: FiatStoreContext }) => {
    // Only persist serializable data — never persist Promises or functions
    const { fiats, mainFiatId, comparisons, exchangeRates } = snapshot.context;
    localStorage.setItem(PERSIST_KEY, JSON.stringify({ fiats, mainFiatId, comparisons, exchangeRates }));
});

// Module-level concurrency guard: Promises are NOT serializable and cannot live in XState context.
let _fetchFiatPromise: Promise<void> | null = null;

const API_BASE = '/api/v1';

export const fiatActions = {
    async fetchFiats(): Promise<void> {
        // If already in-flight, return the same promise — prevents concurrent duplicate requests
        if (_fetchFiatPromise) return _fetchFiatPromise;

        _fetchFiatPromise = (async () => {
            fiatStore.trigger.setLoading({ value: true });
            try {
                await globalActions.fetchFinanceHierarchy();
                const hierarchySnap = globalStore.getSnapshot().context;
                const globalId = hierarchySnap.globalEntityId;
                const currentId = hierarchySnap.entities['current'];
                const customId = hierarchySnap.entities['custom'];

                if (!globalId) {
                    console.error("[FiatStore] Global ID missing. Context entities:", hierarchySnap.entities);
                    throw new Error("Global business entity ID not found");
                }

                // 1. Fetch comparisons from entities that hold exchange-rate records.
                //    The response embeds source_value + target_value with name & expression —
                //    we derive the full Fiat list from these, avoiding entity-hierarchy guessing.
                const fetchComps = async (id: number): Promise<RSComparisonValue[]> => {
                    const { data } = await api.get<{ data: RSComparisonValue[] }>(`/comparison_values/?ref_business_entity=${id}`);
                    return data.data || [];
                };

                const compEntityIds = [currentId, customId].filter((id): id is number => id !== null);
                const uniqueCompIds = [...new Set(compEntityIds)];

                console.log(`[FiatStore] Fetching comparisons from entities: ${uniqueCompIds.join(', ')}`);

                const compResults = await Promise.all(
                    uniqueCompIds.map(id => fetchComps(id).then(list => list.map(c => ({
                        ...c,
                        context: id === currentId ? 'current' : 'custom'
                    }))))
                );

                const comps: Comparison[] = compResults.flat();
                fiatStore.trigger.setComparisons({ data: comps });

                // 2. Extract unique currencies from the embedded source_value / target_value.
                //    This is authoritative: if a currency appears in a comparison, it exists.
                const fiatMap = new Map<number, Fiat>();
                comps.forEach((comp: any) => {
                    [comp.source_value, comp.target_value].forEach((v: any) => {
                        if (v && v.id != null) {
                            const numId = Number(v.id);
                            if (!fiatMap.has(numId)) {
                                fiatMap.set(numId, {
                                    id: numId,
                                    name: v.name,
                                    expression: v.expression
                                });
                            }
                        }
                    });
                });

                const fiatList = Array.from(fiatMap.values());
                fiatStore.trigger.setFiats({ data: fiatList });

                // 3. Fetch main currency option
                const { data: optData } = await api.get<RSOption[]>('/options/?context=global');
                const mainOption = optData.find((o: RSOption) => o.name === 'main_fiat_currency');
                if (mainOption) {
                    fiatStore.trigger.setMainFiat({ id: parseInt(mainOption.value) });
                }

                // 4. Build exchange rate map — always use Number() to avoid string/number mismatches
                const rates: Record<number, number> = {};
                const mainId = Number(fiatStore.getSnapshot().context.mainFiatId);
                if (mainId && comps.length) {
                    comps.forEach(comp => {
                        const from = Number(comp.value_from);
                        const to = Number(comp.value_to);
                        if (from === mainId) {
                            rates[to] = comp.quantity_to / comp.quantity_from;
                        } else if (to === mainId) {
                            rates[from] = comp.quantity_from / comp.quantity_to;
                        }
                    });
                }
                fiatStore.trigger.setExchangeRates({ rates });

                console.log("[FiatStore] Successfully fetched context.", {
                    fiats: fiatList.length,
                    comparisons: comps.length,
                    rates: Object.keys(rates).length
                });

            } catch (error) {
                console.error("[FiatStore] Failed to fetch fiats: ", error);
            } finally {
                fiatStore.trigger.setLoading({ value: false });
                _fetchFiatPromise = null;
            }
        })();

        return _fetchFiatPromise;
    },

    async setMainFiat(id: number): Promise<boolean> {
        try {
            const { data: optData } = await api.get<RSOption[]>('/options/?context=global');
            const mainOption = optData.find((o: RSOption) => o.name === 'main_fiat_currency');

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
