from abc import ABC, abstractmethod
from typing import Optional, List
from domain.entities import Produto, ItemKit

class ProdutoRepository(ABC): # pragma: no cover
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
    def atualizar(self, produto: Produto, on_not_found: Exception, on_outdated_version: Exception, on_duplicate: Exception):
        pass

    @abstractmethod
    def busca_lista_item_kit(self, kit_id: int) -> Optional[List[ItemKit]]:
        pass
