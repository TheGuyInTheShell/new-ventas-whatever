export interface InventoryItem {
    id: number;
    uid: string;
    name: string;
    type: string;
    expression: string;
    identifier?: string;
    comparison_id: number | null;
    quantity_from: number;
    quantity_to: number;
    value_to: number | null;
    balance: number;
    balance_id?: number;
    ref_super_values_ids: number[];
    meta: Array<{ key: string; value: string }>;
    prices?: Array<{
        comparison_id: number;
        quantity_to: number;
        quantity_from: number;
        fiat_id: number;
    }>;
}

export interface InventoryStoreContext {
    items: InventoryItem[];
    eligibleItems: InventoryItem[];
    loading: boolean;
    error: string | null;
}

export interface InventoryStoreEventPayloads {
    setLoading: { value: boolean };
    setItems: { data: InventoryItem[] };
    setEligibleItems: { data: InventoryItem[] };
    setError: { message: string | null };
}
