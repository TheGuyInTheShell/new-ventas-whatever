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
    
    // Split balances
    basic_balance: number;
    basic_balance_id?: number;
    adjustment_balance: number;
    adjustment_balance_id?: number;
    
    // Legacy support
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
