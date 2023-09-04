from abc import ABC, abstractmethod
from domain.models import Produto

class ProdutoRepository(ABC):
    @abstractmethod
    def inserir(self, produto: Produto, on_duplicate_sku: Exception):
        pass

    @abstractmethod
    def buscarPorSku(self, sku: str, on_not_found: Exception) -> Produto:
        pass

    @abstractmethod
    def excluir(self, sku: str, on_not_found: Exception):
        pass

    @abstractmethod
    def atualizar(self, produto: Produto, on_not_found: Exception):
        pass
