from fastapi import APIRouter, HTTPException
from typing import List
from domain.models import Produto, ItemKit
from domain.exceptions import *
from domain.services import CatalogoService

class HTTPAPIAdapter:
    def __init__(self, catalogo_service: CatalogoService):
        self.__catalogo_service = catalogo_service
        self.router = APIRouter()
        self.router.add_api_route("/produto", self.criar_produto, methods=["POST"])
        self.router.add_api_route("/produto/{sku}", self.obter_produto, methods=["GET"])
        self.router.add_api_route("/produto/{sku}", self.atualizar_produto, methods=["PUT"])
        self.router.add_api_route("/produto/{sku}", self.deletar_produto, methods=["DELETE"])
        self.router.add_api_route("/item-kit", self.criar_item_kit, methods=["POST"])
        self.router.add_api_route("/item-kit/{id}", self.obter_item_kit, methods=["GET"])
        self.router.add_api_route("/item-kit/{id}", self.atualizar_item_kit, methods=["PUT"])
        self.router.add_api_route("/item-kit/{id}", self.deletar_item_kit, methods=["DELETE"])
        self.router.add_api_route("/produto/{sku}/kit", self.vincular_lista_item_kit, methods=["PUT"])

    def criar_produto(self, novo_produto: Produto):
        try:
            self.__catalogo_service.criar_produto(novo_produto)
            return {"message": "Produto criado com sucesso"}
        except (SkuInvalido, ProdutoInvalido, PrecoInvalido, EstoqueInvalido) as e:
            raise HTTPException(status_code=400, detail=f"Erro ao criar produto: {e}")
        except ProdutoJaExiste as e:
            raise HTTPException(status_code=409, detail=f"Erro ao criar produto: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao criar produto: {e}")
    
    def obter_produto(self, sku: str):
        try:
            return self.__catalogo_service.obter_produto(sku)
        except SkuInvalido as e:
            raise HTTPException(status_code=400, detail=f"Erro ao obter produto: {e}")
        except ProdutoNaoEncontrado as e:
            raise HTTPException(status_code=404, detail=f"Erro ao obter produto: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao obter produto: {e}")

    def atualizar_produto(self, sku: str, atualiza_produto: Produto):
        try:
            self.__catalogo_service.atualizar_produto(sku, atualiza_produto)
            return {"message": "Produto atualizado com sucesso"}
        except (SkuInvalido, ProdutoInvalido, PrecoInvalido, EstoqueInvalido) as e:
            raise HTTPException(status_code=400, detail=f"Erro ao atualizar produto: {e}")
        except ProdutoNaoEncontrado as e:
            raise HTTPException(status_code=404, detail=f"Erro ao atualizar produto: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao atualizar produto: {e}")
        
    def deletar_produto(self, sku: str):
        try:
            self.__catalogo_service.deletar_produto(sku)
            return {"message": "Produto deletado com sucesso"}
        except SkuInvalido as e:
            raise HTTPException(status_code=400, detail=f"Erro ao deletar produto: {e}")
        except ProdutoNaoEncontrado as e:
            raise HTTPException(status_code=404, detail=f"Erro ao deletar produto: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao deletar produto: {e}")
        
    def obter_item_kit(self, id: int):
        try:
            return self.__catalogo_service.obter_item_kit(id)
        except ItemKitNaoEncontrado as e:
            raise HTTPException(status_code=404, detail=f"Erro ao obter item de kit: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao obter item de kit: {e}")
        
    def criar_item_kit(self, item_kit: ItemKit):
        try:
            return self.__catalogo_service.criar_item_kit(item_kit)
        except (ItemKitInvalido, PrecoInvalido) as e:
            raise HTTPException(status_code=400, detail=f"Erro ao criar item de kit: {e}")
        except ProdutoNaoEncontrado as e:
            raise HTTPException(status_code=404, detail=f"Produto não encontrado: {e}")
        except ItemKitJaExiste as e:
            raise HTTPException(status_code=409, detail=f"Item Kit já existente: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao criar item de kit: {e}")
    
    def atualizar_item_kit(self, id:int, item_kit: ItemKit):
        try:
            self.__catalogo_service.atualizar_item_kit(id, item_kit)
            return {"message": "Item de kit atualizado com sucesso"}
        except (ItemKitInvalido, PrecoInvalido, ListaItemKitInvalida) as e:
            raise HTTPException(status_code=400, detail=f"Erro ao atualizar item de kit: {e}")
        except ProdutoNaoEncontrado as e:
            raise HTTPException(status_code=404, detail=f"Produto não encontrado: {e}")
        except ItemKitNaoEncontrado as e:
            raise HTTPException(status_code=404, detail=f"Item de kit não encontrado: {e}")
        except ErroListaInexistente as e:
            raise HTTPException(status_code=500, detail=f"Lista de item de kit não encontrada: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao atualizar item de kit: {e}")
        
    def deletar_item_kit(self, id: int):
        try:
            self.__catalogo_service.deletar_item_kit(id)
            return {"message": "Item de kit deletado com sucesso"}
        except ItemKitInvalido as e:
            raise HTTPException(status_code=400, detail=f"Erro ao deletar item de kit: {e}")
        except ItemKitNaoEncontrado as e:
            raise HTTPException(status_code=404, detail=f"Item de kit não encontrado: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao deletar item de kit: {e}")
        
    def vincular_lista_item_kit(self, sku: str, lista_item_kit: List[ItemKit]):
        try:
            self.__catalogo_service.vincular_lista_item_kit(sku, lista_item_kit)
            return {"message": "Lista de item de kit vinculada com sucesso"}
        except (SkuInvalido, ListaItemKitInvalida) as e:
            raise HTTPException(status_code=400, detail=f"Erro ao vincular lista de item de kit: {e}")
        except ProdutoNaoEncontrado as e:
            raise HTTPException(status_code=404, detail=f"Produto não encontrado: {e}")
        except ItemKitNaoEncontrado as e:
            raise HTTPException(status_code=404, detail=f"Item de kit não encontrado: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao vincular lista de item de kit: {e}")