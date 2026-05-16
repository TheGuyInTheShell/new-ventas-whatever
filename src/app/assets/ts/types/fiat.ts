export interface Fiat {
    id: number;
    name: string;
    expression: string;
}

export interface Comparison {
    id: number;
    value_from: number;
    value_to: number;
    quantity_from: number;
    quantity_to: number;
    ref_business_entity: number;
    context: string;
}

export interface FiatStoreContext {
    fiats: Fiat[];
    mainFiatId: number | null;
    comparisons: Comparison[];
    exchangeRates: Record<number, number>;
    loading: boolean;
    // NOTE: fetchingPromise must NOT be here — Promises are not serializable.
    // The concurrency guard lives as a module-level variable in fiatStore.ts.
}

export interface FiatStoreEventPayloads {
    setLoading: { value: boolean };
    setFiats: { data: Fiat[] };
    setMainFiat: { id: number };
    setComparisons: { data: Comparison[] };
    setExchangeRates: { rates: Record<number, number> };
}
