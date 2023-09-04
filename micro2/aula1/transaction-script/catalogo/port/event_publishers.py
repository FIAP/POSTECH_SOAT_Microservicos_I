from abc import ABC, abstractmethod
from domain.models import Produto

class ProdutoEventPublisher(ABC):
    @abstractmethod
    def publicar(self, produto: Produto):
        pass