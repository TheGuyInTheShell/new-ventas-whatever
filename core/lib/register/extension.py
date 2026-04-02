from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

class Extension(ABC):
    app: 'FastAPI'
    
    def __init__(self, app: 'FastAPI'):
        self.app = app

    @abstractmethod
    def extends(self):
        pass