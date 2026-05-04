/**
 * Core API response structures mirroring backend Pydantic schemas.
 */

export interface RSMeta {
    key: string;
    value: string;
}

export interface RSBalance {
    id: number;
    quantity: number;
    type: 'basic' | 'adjustment';
}

export interface RSValue {
    id: number;
    uid: string;
    name: string;
    type: string;
    expression: string;
    identifier?: string;
    ref_business_entity: number;
    meta?: RSMeta[];
    balances?: RSBalance[];
    ref_super_values_ids?: number[];
}

export interface RSComparisonValue {
    id: number;
    uid: string;
    quantity_from: number;
    quantity_to: number;
    value_from: number;
    value_to: number;
    ref_business_entity: number;
}

/**
 * Structure returned by the values_with_comparison query endpoint
 */
export interface RSQueryValueWithComparison {
    value: RSValue[];
    comparison_value?: RSComparisonValue[];
}

export interface ApiError {
    message: string;
    code?: string;
    detail?: any;
}

export interface ServiceResult<T> {
    data: T | null;
    error: ApiError | null;
}
