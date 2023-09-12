from abc import ABC, abstractmethod
from typing import Optional, List
from domain.entities import Produto, ItemKit

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

    @abstractmethod
    def inserir_item_kit(self, item_kit: ItemKit, on_duplicate_id: Exception, on_not_found: Exception) -> int:
        pass

    @abstractmethod
    def atualizar_item_kit(self, item_kit: ItemKit, on_not_found: Exception, on_outdated_version: Exception):
        pass

    @abstractmethod
    def buscar_item_kit_por_id(self, id: int, on_not_found: Exception) -> ItemKit:
        pass

    @abstractmethod
    def excluir_item_kit(self, id: int, on_not_found: Exception):
        pass

    @abstractmethod
    def busca_lista_item_kit(self, kit_id: int) -> Optional[List[ItemKit]]:
        pass

    @abstractmethod
    def vincular_lista_item_kit(self, kit_id: int, lista_item_kit_id: List[ItemKit], on_not_found:Exception):
        pass