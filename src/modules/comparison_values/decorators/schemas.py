from pydantic import BaseModel, ConfigDict
from typing import Any, List, Optional

class RQComparisonValueDecorator(BaseModel):
    ref_comparation_values_from: int
    ref_comparation_values_to: int
    comparison_decorators: Optional[dict[str, Any]] = None
    is_reactive: bool = False

    model_config = ConfigDict(from_attributes=True)

class RSComparisonValueDecorator(BaseModel):
    ref_comparation_values_from: int
    ref_comparation_values_to: int
    comparison_decorators: Optional[dict[str, Any]] = None
    is_reactive: bool = False

    model_config = ConfigDict(from_attributes=True)

class RSComparisonValueDecoratorList(BaseModel):
    data: List[RSComparisonValueDecorator]
    total: int
    page: int
    page_size: int
    total_pages: int
