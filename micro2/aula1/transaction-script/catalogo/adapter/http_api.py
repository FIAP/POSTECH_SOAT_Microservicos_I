from fastapi import APIRouter, HTTPException
from domain.models import Produto
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
    def criar_produto(self, novo_produto: Produto):
        try:
            self.__catalogo_service.criar_produto(novo_produto)
            return {"message": "Produto criado com sucesso"}
        except (SkuInvalido, ProdutoInvalido) as e:
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
        except (SkuInvalido, ProdutoInvalido) as e:
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