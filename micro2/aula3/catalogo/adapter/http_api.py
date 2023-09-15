from fastapi import APIRouter, HTTPException
from typing import List
from domain.entities import Produto, ItemKit
from domain.value_objects import ItemKitDetalhe, Estoque, Preco
from domain.exceptions import *
from domain.services import CatalogoService
from adapter.dto import ProdutoRequestDTO, ProdutoResponseDTO, ItemKitRequestDTO, ItemKitResponseDTO, ItemKitDetalheRequestDTO, PrecoDTO, EstoqueDTO, ItemKitDTO

class HTTPAPIAdapter:
    def __init__(self, catalogo_service: CatalogoService):
        self.__catalogo_service = catalogo_service
        self.router = APIRouter()
        self.router.add_api_route("/produto", self.criar_produto, methods=["POST"])
        self.router.add_api_route("/produto/{sku}", self.obter_produto, methods=["GET"])
        self.router.add_api_route("/produto/{sku}", self.atualizar_produto, methods=["PUT"])
        self.router.add_api_route("/produto/{sku}", self.deletar_produto, methods=["DELETE"])
        self.router.add_api_route("/produto/{sku}/item-kit", self.criar_item_kit, methods=["POST"])
        self.router.add_api_route("/produto/{sku}/item-kit/{produtoId}", self.obter_item_kit, methods=["GET"])
        self.router.add_api_route("/produto/{sku}/item-kit/{produtoId}", self.atualizar_item_kit, methods=["PUT"])
        self.router.add_api_route("/produto/{sku}/item-kit/{produtoId}", self.deletar_item_kit, methods=["DELETE"])

    def criar_produto(self, novo_produto: ProdutoRequestDTO):
        try:
            estoque = None
            preco = None
            if novo_produto.estoque is not None:
                estoque = Estoque(emEstoque=novo_produto.estoque.emEstoque, reservado=novo_produto.estoque.reservado)
            if novo_produto.preco is not None:
                preco = Preco(precoLista=novo_produto.preco.precoLista, precoDesconto=novo_produto.preco.precoDesconto)
            self.__catalogo_service.criar_produto(sku=novo_produto.sku, nome=novo_produto.nome, descr=novo_produto.descr, 
                              urlImagem=novo_produto.urlImagem, preco=preco, estoque=estoque)
            return {"message": "Produto criado com sucesso"}
        except (SkuInvalido, ProdutoInvalido, PrecoInvalido, EstoqueInvalido) as e:
            raise HTTPException(status_code=400, detail=f"Erro ao criar produto: {e}")
        except (ProdutoJaExiste, ProdutoOuItemKitDuplicado) as e:
            raise HTTPException(status_code=409, detail=f"Erro ao criar produto: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao criar produto: {e}")
    
    def obter_produto(self, sku: str):
        try:
            produto = self.__catalogo_service.obter_produto(sku)
            estoque = None
            preco = None
            if produto.preco is not None:
                preco = PrecoDTO(precoLista=produto.preco.precoLista, precoDesconto=produto.preco.precoDesconto)
            if produto.estoque is not None:
                estoque = EstoqueDTO(emEstoque=produto.estoque.emEstoque, reservado=produto.estoque.reservado)
            kit = []
            for itemKit in produto.kit:
                precoItemKit = PrecoDTO(precoLista=itemKit.preco.precoLista, precoDesconto=itemKit.preco.precoDesconto)
                kit.append(ItemKitDTO(produtoId=itemKit.produtoId, qtd=itemKit.qtd, preco=precoItemKit))
            return ProdutoResponseDTO(id=produto.id, sku=produto.sku, nome=produto.nome, descr=produto.descr, 
                                      urlImagem=produto.urlImagem, preco=preco, estoque=estoque, kit=kit)
        except SkuInvalido as e:
            raise HTTPException(status_code=400, detail=f"Erro ao obter produto: {e}")
        except ProdutoNaoEncontrado as e:
            raise HTTPException(status_code=404, detail=f"Erro ao obter produto: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao obter produto: {e}")

    def atualizar_produto(self, sku: str, atualiza_produto: ProdutoRequestDTO):
        try:
            estoque = None
            preco = None
            if atualiza_produto.estoque is not None:
                estoque = Estoque(emEstoque=atualiza_produto.estoque.emEstoque, reservado=atualiza_produto.estoque.reservado)
            if atualiza_produto.preco is not None:
                preco = Preco(precoLista=atualiza_produto.preco.precoLista, precoDesconto=atualiza_produto.preco.precoDesconto)
            self.__catalogo_service.atualizar_produto(sku=sku, nome=atualiza_produto.nome, descr=atualiza_produto.descr, 
                              urlImagem=atualiza_produto.urlImagem, preco=preco, estoque=estoque)
            return {"message": "Produto atualizado com sucesso"}
        except (SkuInvalido, ProdutoInvalido, PrecoInvalido, EstoqueInvalido) as e:
            raise HTTPException(status_code=400, detail=f"Erro ao atualizar produto: {e}")
        except ProdutoNaoEncontrado as e:
            raise HTTPException(status_code=404, detail=f"Erro ao atualizar produto: {e}")
        except ProdutoDesatualizado as e:
            raise HTTPException(status_code=409, detail=f"Produto desatualizado: {e}")
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
        
    def obter_item_kit(self, sku: str, produtoId: int):
        try:
            itemKit = self.__catalogo_service.obter_item_kit(sku, produtoId)
            preco = None
            if itemKit.preco is not None:
                preco = PrecoDTO(precoLista=itemKit.preco.precoLista, precoDesconto=itemKit.preco.precoDesconto)
            return ItemKitResponseDTO(id=itemKit.id, kitId=itemKit.kitId, produtoId=itemKit.produtoId, qtd=itemKit.qtd, preco=preco)
        except ItemKitNaoEncontrado as e:
            raise HTTPException(status_code=404, detail=f"Erro ao obter item de kit: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao obter item de kit: {e}")
        
    def criar_item_kit(self, sku: str, listaItemKitRequestDTO: List[ItemKitRequestDTO]):
        try:
            listaItemKitDetalhe = []
            for itemKitRequestDTO in listaItemKitRequestDTO:
                preco = None
                if itemKitRequestDTO.preco is not None:
                    preco = PrecoDTO(precoLista=itemKitRequestDTO.preco.precoLista, precoDesconto=itemKitRequestDTO.preco.precoDesconto)
                itemKitDetalhe = ItemKitDetalhe(produtoId=itemKitRequestDTO.produtoId, qtd=itemKitRequestDTO.qtd, preco=preco)
                listaItemKitDetalhe.append(itemKitDetalhe)
            self.__catalogo_service.inserir_lista_item_kit(sku, listaItemKitDetalhe)
            return {"message": "Item de kit criado com sucesso"}
        except (ItemKitInvalido, PrecoInvalido, ListaItemKitInvalida) as e:
            raise HTTPException(status_code=400, detail=f"Erro ao criar item de kit: {e}")
        except ProdutoNaoEncontrado as e:
            raise HTTPException(status_code=404, detail=f"Produto não encontrado: {e}")
        except ProdutoOuItemKitDuplicado as e:
            raise HTTPException(status_code=409, detail=f"Item Kit já existente: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao criar item de kit: {e}")
    
    def atualizar_item_kit(self, sku: str, produtoId: int, itemKitDetalheRequestDTO: ItemKitDetalheRequestDTO):
        try:
            preco = None
            if itemKitDetalheRequestDTO.preco is not None:
                preco = PrecoDTO(precoLista=itemKitDetalheRequestDTO.preco.precoLista, precoDesconto=itemKitDetalheRequestDTO.preco.precoDesconto)
            self.__catalogo_service.atualizar_item_kit(sku=sku, produtoId=produtoId, qtd=itemKitDetalheRequestDTO.qtd, preco=preco)
            return {"message": "Item de kit atualizado com sucesso"}
        except (ItemKitInvalido, PrecoInvalido, ListaItemKitInvalida) as e:
            raise HTTPException(status_code=400, detail=f"Erro ao atualizar item de kit: {e}")
        except ProdutoNaoEncontrado as e:
            raise HTTPException(status_code=404, detail=f"Produto não encontrado: {e}")
        except ItemKitNaoEncontrado as e:
            raise HTTPException(status_code=404, detail=f"Item de kit não encontrado: {e}")
        except ProdutoDesatualizado as e:
            raise HTTPException(status_code=409, detail=f"Produto desatualizado: {e}")
        except ErroListaInexistente as e:
            raise HTTPException(status_code=500, detail=f"Lista de item de kit não encontrada: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao atualizar item de kit: {e}")
        
    def deletar_item_kit(self, sku: str, produtoId: int):
        try:
            self.__catalogo_service.deletar_item_kit(sku, produtoId)
            return {"message": "Item de kit deletado com sucesso"}
        except ItemKitInvalido as e:
            raise HTTPException(status_code=400, detail=f"Erro ao deletar item de kit: {e}")
        except ItemKitNaoEncontrado as e:
            raise HTTPException(status_code=404, detail=f"Item de kit não encontrado: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao deletar item de kit: {e}")