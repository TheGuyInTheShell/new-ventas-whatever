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
    ref_super_values_ids: number[];
    meta: Array<{ key: string; value: string }>;
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
