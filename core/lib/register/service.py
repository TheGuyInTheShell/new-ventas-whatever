from abc import ABC

class Service(ABC):
    """
    Base class for all business logic services.
    
    Services should encapsulate domain logic, data access orchestration,
    and business rules, separating them from the transport/controller layer.
    """
    def __init__(self) -> None:
        pass