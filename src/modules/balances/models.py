from sqlalchemy import String, Integer, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import BaseAsync
from src.modules.values.models import Value


class Balance(BaseAsync):
    __tablename__ = "balances"
    
    type: Mapped[str] = mapped_column(String, nullable=False)
    
    quantity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    ref_value: Mapped[int] = mapped_column(
        Integer, ForeignKey("values.id"), nullable=False
    )
    
    value: Mapped["Value"] = relationship("Value", back_populates="balances")
