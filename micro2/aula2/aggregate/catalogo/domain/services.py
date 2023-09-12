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
            self.__produto_repository.atualizar(produto, on_not_found=ProdutoNaoEncontrado("Produto não encontrado"), 
                                                         on_outdated_version=ProdutoDesatualizado("Produto desatualizado"), 
                                                         on_duplicate=ProdutoOuItemKitDuplicado("Produto ou item de kit duplicado"))
            self.__produto_event_publisher.publicar(produto)
        except (ProdutoOuItemKitDuplicado, SkuInvalido, PrecoInvalido, EstoqueInvalido, ProdutoInvalido, ProdutoNaoEncontrado):
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
        
    def inserir_lista_item_kit(self, sku: str, listaItemKitDetalhe: List['ItemKitDetalhe']):
        try:
            Produto.validarSku(sku)
            produto = self.__produto_repository.buscarPorSku(sku, on_not_found=ProdutoNaoEncontrado("Produto não encontrado"))
            produto.inserirListaItemKit(listaItemKitDetalhe)
            self.__produto_repository.atualizar(produto, on_not_found=ProdutoNaoEncontrado("Produto não encontrado"), 
                                                         on_outdated_version=ProdutoInvalido("Produto desatualizado"), 
                                                         on_duplicate=ProdutoOuItemKitDuplicado("Produto ou item de kit duplicado"))
        except (ProdutoOuItemKitDuplicado, ListaItemKitInvalida, ProdutoNaoEncontrado, ProdutoNaoEncontrado, SkuInvalido, ItemKitInvalido, ItemKitNaoEncontrado, ItemKitJaExiste, PrecoInvalido, ProdutoNaoEncontrado, SkuInvalido):
            raise
        except Exception as e:
            raise ErroAoCriarItemKit(f"Erro ao criar item de kit: {e}")
    
    def atualizar_item_kit(self, sku: str, produtoId: int, qtd: int, preco: Preco):
        try:
            Produto.validarSku(sku)
            produto = self.__produto_repository.buscarPorSku(sku, on_not_found=ProdutoNaoEncontrado("Produto não encontrado"))
            produto.atualizarItemKit(produtoId, qtd, preco)
            self.__produto_repository.atualizar(produto, on_not_found=ProdutoNaoEncontrado("Produto não encontrado"), 
                                                         on_outdated_version=ProdutoDesatualizado("Produto desatualizado"), 
                                                         on_duplicate=ProdutoOuItemKitDuplicado("Produto ou item de kit duplicado"))
        except (ProdutoOuItemKitDuplicado, ProdutoDesatualizado, ItemKitInvalido, ListaItemKitInvalida, ItemKitNaoEncontrado, PrecoInvalido, ProdutoNaoEncontrado, ProdutoNaoEncontrado, SkuInvalido):
            raise
        except Exception as e:
            raise ErroAoAtualizarItemKit(f"Erro ao atualizar item de kit: {e}")
    
    def obter_item_kit(self, sku: str, produtoId: int) -> ItemKit:
        try:
            Produto.validarSku(sku)
            produto = self.__produto_repository.buscarPorSku(sku, on_not_found=ProdutoNaoEncontrado("Produto não encontrado"))                
            return produto.obterItemKit(produtoId)
        except (ProdutoNaoEncontrado, ItemKitInvalido, ItemKitNaoEncontrado):
            raise
        except Exception as e:
            raise ErroAoObterItemKit(f"Erro ao obter item kit: {e}")
    
    def deletar_item_kit(self, sku: str, produtoId: int):
        try:
            Produto.validarSku(sku)
            produto = self.__produto_repository.buscarPorSku(sku, on_not_found=ProdutoNaoEncontrado("Produto não encontrado"))
            produto.removerItemKit(produtoId)
            self.__produto_repository.atualizar(produto, on_not_found=ProdutoNaoEncontrado("Produto não encontrado"), 
                                                         on_outdated_version=ProdutoDesatualizado("Produto desatualizado"), 
                                                         on_duplicate=ProdutoOuItemKitDuplicado("Produto ou item de kit duplicado"))
            return {"message": "Item de kit deletado com sucesso"}
        except (ProdutoDesatualizado, ProdutoNaoEncontrado, ItemKitInvalido, ItemKitNaoEncontrado):
            raise
        except Exception as e:
            raise ErroAoDeletarItemKit(f"Erro ao deletar item de kit: {e}")
