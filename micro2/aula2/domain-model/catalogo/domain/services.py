from typing import List
from domain.entities import Produto, ItemKit
from domain.value_objects import ItemKitDetalhe, Preco, Estoque
from domain.exceptions import *
from port.repositories import ProdutoRepository
from port.event_publishers import ProdutoEventPublisher

class CatalogoService:
    def __init__(self, produto_repository: ProdutoRepository, produto_event_publisher: ProdutoEventPublisher):
        self.__produto_repository = produto_repository
        self.__produto_event_publisher = produto_event_publisher     
        
    def criar_produto(self, sku: str, nome: str, descr: str, urlImagem: str, preco: Preco, estoque: Estoque):
        try:
            produto = Produto(sku=sku, nome=nome, descr=descr, 
                              urlImagem=urlImagem, preco=preco, estoque=estoque)
            self.__produto_repository.inserir(produto, on_duplicate_sku=ProdutoJaExiste("Produto já existente"))
            self.__produto_event_publisher.publicar(produto)
        except (SkuInvalido, PrecoInvalido, EstoqueInvalido, ProdutoInvalido, ProdutoJaExiste):
            raise
        except Exception as e:
            raise ErroAoCriarProduto(f"Erro ao criar produto: {e}")

    def obter_produto(self, sku: str) -> Produto:
        try:
            Produto.validarSku(sku)
            produto = self.__produto_repository.buscarPorSku(sku, on_not_found=ProdutoNaoEncontrado("Produto não encontrado"))
            if produto is None:
                raise ProdutoNaoEncontrado(f"Produto não encontrado")
            lista_item_kit = self.__produto_repository.busca_lista_item_kit(produto.id)
            produto.setKit(lista_item_kit)
            return produto
        except (SkuInvalido, ProdutoNaoEncontrado):
            raise
        except Exception as e:
            raise ErroAoObterProduto(f"Erro ao obter produto: {e}")

    def atualizar_produto(self, sku: str, nome: str, descr: str, urlImagem: str, preco: Preco, estoque: Estoque):
        try:
            produto = Produto(sku=sku, nome=nome, descr=descr, 
                              urlImagem=urlImagem, preco=preco, estoque=estoque)
            self.__produto_repository.atualizar(produto, on_not_found=ProdutoNaoEncontrado("Produto não encontrado"))
            self.__produto_event_publisher.publicar(produto)
        except (SkuInvalido, PrecoInvalido, EstoqueInvalido, ProdutoInvalido, ProdutoNaoEncontrado):
            raise
        except Exception as e:
            raise ErroAoAtualizarProduto(f"Erro ao atualizar produto: {e}")

    def deletar_produto(self, sku: str):
        try:
            Produto.validarSku(sku)
            self.__produto_repository.excluir(sku, on_not_found=ProdutoNaoEncontrado("Produto não encontrado"))
            return {"message": "Produto deletado com sucesso"}
        except (SkuInvalido, ProdutoNaoEncontrado):
            raise
        except Exception as e:
            raise ErroAoDeletarProduto(f"Erro ao deletar produto: {e}")
        
    def criar_item_kit(self, produtoId: int, qtd: int, preco: Preco) -> ItemKit:
        try:
            itemKit = ItemKit(produtoId=produtoId, qtd=qtd, preco=preco)
            itemKitId = self.__produto_repository.inserir_item_kit(itemKit, on_duplicate_id=ItemKitJaExiste("Item de kit já existente"), on_not_found=ProdutoNaoEncontrado("Produto não encontrado"))
            return self.__produto_repository.buscar_item_kit_por_id(itemKitId, on_not_found=ItemKitNaoEncontrado("Item de kit não encontrado"))
        except (ItemKitInvalido, ItemKitNaoEncontrado, ItemKitJaExiste, PrecoInvalido, ProdutoNaoEncontrado):
            raise
        except Exception as e:
            raise ErroAoCriarItemKit(f"Erro ao criar item de kit: {e}")
    
    def atualizar_item_kit(self, id:int, qtd: int, preco: Preco):
        try:
            if id < 0:
                raise ItemKitInvalido("Id não pode ser negativo")
            itemKitDetalhe = ItemKitDetalhe(qtd=qtd, preco=preco)
            itemKit = self.__produto_repository.buscar_item_kit_por_id(id, on_not_found=ItemKitNaoEncontrado("Item de kit não encontrado"))
            listaItemKit = None
            if itemKit.kitId is not None:        
                listaItemKit = self.__produto_repository.busca_lista_item_kit(itemKit.kitId)
            itemKit.atualizar(itemKitDetalhe, listaItemKit)
            self.__produto_repository.atualizar_item_kit(itemKit, on_not_found=ProdutoNaoEncontrado("Produto não encontrado"), on_outdated_version=ItemKitInvalido("Item de kit desatualizado"))
        except (ItemKitInvalido, ListaItemKitInvalida, ItemKitNaoEncontrado, PrecoInvalido, ProdutoNaoEncontrado):
            raise
        except Exception as e:
            raise ErroAoAtualizarItemKit(f"Erro ao atualizar item de kit: {e}")
    
    def obter_item_kit(self, id: int) -> ItemKit:
        try:
            if id < 0:
                raise ItemKitInvalido("Id não pode ser negativo")
            item_kit = self.__produto_repository.buscar_item_kit_por_id(id, on_not_found=ItemKitNaoEncontrado("Item de kit não encontrado"))
            if item_kit is None:
                raise ItemKitNaoEncontrado(f"Item de kit não encontrado")
            return item_kit
        except (ItemKitInvalido, ItemKitNaoEncontrado):
            raise
        except Exception as e:
            raise ErroAoObterItemKit(f"Erro ao obter item kit: {e}")
    
    def deletar_item_kit(self, id: int):
        try:
            if id < 0:
                raise ItemKitInvalido("Id não pode ser negativo")
            self.__produto_repository.excluir_item_kit(id, on_not_found=ItemKitNaoEncontrado("Item de kit não encontrado"))
            return {"message": "Item de kit deletado com sucesso"}
        except (ItemKitInvalido, ItemKitNaoEncontrado):
            raise
        except Exception as e:
            raise ErroAoDeletarItemKit(f"Erro ao deletar item de kit: {e}")
        
    def vincular_lista_item_kit(self, sku: str, lista_item_kit_id: List[int]):
        try:
            Produto.validarSku(sku)
            produto = self.__produto_repository.buscarPorSku(sku, on_not_found=ProdutoNaoEncontrado("Produto não encontrado"))
            lista_item_kit_atual = []
            for item_kit_id in lista_item_kit_id:
                item_kit_atual = self.__produto_repository.buscar_item_kit_por_id(item_kit_id, on_not_found=ItemKitNaoEncontrado(f"Item de kit não encontrado: {item_kit_id}"))
                item_kit_atual.setKitId(produto.id)
                lista_item_kit_atual.append(item_kit_atual)
            produto.vincularListaItemKit(lista_item_kit_atual)
            self.__produto_repository.vincular_lista_item_kit(produto.id, lista_item_kit_atual, on_not_found=ProdutoNaoEncontrado("Produto Kit não encontrado"))
        except (ProdutoNaoEncontrado, SkuInvalido, ItemKitNaoEncontrado, ListaItemKitInvalida):
            raise
        except Exception as e:
            raise ErroAoVincularItemKit(f"Erro ao vincular item de kit: {e}")