from typing import Optional, List, Union
from pydantic import BaseModel
from src.modules.values.schemas import RQValue, RSValue
from src.modules.comparison_values.schemas import RQComparisonValue, RSComparisonValue


class RQValueWithComparison(BaseModel):
    value: RQValue
    comparison_value: RQComparisonValue
    ref_super_values_ids: Optional[List[int]] = []
    business_entity_ids: Optional[List[int]] = []
    balance_type: Optional[str] = None


class RSValueWithComparison(BaseModel):
    value: RSValue
    comparison_value: RSComparisonValue
    ref_super_values_ids: Optional[List[int]] = []
    business_entity_ids: Optional[List[int]] = []


class QueryValue(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    expression: Optional[str] = None
    identifier: Optional[str] = None
    type: Optional[str] = None
    price: Optional[float] = None
    meta: Optional[List[int]] = None
    full_meta: bool = False


class QueryComparisonValue(BaseModel):
    id: Optional[int] = None
    ref_business_entity: Optional[int] = None
    quantity_from: Optional[float] = None
    quantity_to: Optional[float] = None
    value_from: Optional[int] = None
    value_to: Optional[int] = None
    meta: Optional[List[int]] = None
    full_meta: bool = False


class QueryValuesWithComparison(BaseModel):
    value: Optional[QueryValue] = None
    comparison_value: Optional[QueryComparisonValue] = None
    ref_business_entity: Optional[int] = None
    ref_super_values_ids: Optional[List[int]] = (
        None  # filter: only values that are children of these parents
    )


class RSValueWithHierarchy(RSValue):
    """RSValue extended with its parent hierarchy IDs."""

    ref_super_values_ids: List[int] = []


class ResultValueWithComparison(BaseModel):
    value: Optional[List[RSValueWithHierarchy]] = None
    comparison_value: Optional[List[RSComparisonValue]] = None
