from abc import ABC, abstractmethod
from domain.entities import Produto

class ProdutoEventPublisher(ABC):
    @abstractmethod
    def publicar(self, produto: Produto):
        pass