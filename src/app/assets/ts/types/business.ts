export interface BusinessEntityStoreContext {
    entityId: number | null;
    inventoryId: number | null;
    loading: boolean;
    fetchingPromise: Promise<void> | null;
    error: string | null;
}

export interface BusinessEntityStoreEventPayloads {
    setEntityId: { id: string | number | null };
    setInventoryId: { id: string | number | null };
    setLoading: { value: boolean };
    setFetchingPromise: { promise: Promise<void> | null };
    setError: { message: string | null };
}
