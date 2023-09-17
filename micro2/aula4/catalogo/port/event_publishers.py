from abc import ABC, abstractmethod
from domain.entities import Produto

class ProdutoEventPublisher(ABC): # pragma: no cover
    @abstractmethod
    def publicar(self, produto: Produto):
        pass