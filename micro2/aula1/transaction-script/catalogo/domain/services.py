from typing import List
from domain.models import Produto, Preco, Estoque, ItemKit
from domain.exceptions import *
from port.repositories import ProdutoRepository
from port.event_publishers import ProdutoEventPublisher

class CatalogoService:
    def __init__(self, produto_repository: ProdutoRepository, produto_event_publisher: ProdutoEventPublisher):
        self.__produto_repository = produto_repository
        self.__produto_event_publisher = produto_event_publisher
    
    def __validar_estoque(self, estoque: Estoque):
        if estoque is not None and estoque.emEstoque is None:
            raise EstoqueInvalido("Campo emEstoque é obrigatório")
        if estoque.emEstoque < 0:
            raise EstoqueInvalido("Campo emEstoque não pode ser negativo")
        if estoque.reservado < 0:
            raise EstoqueInvalido("Campo reservado não pode ser negativo")
        
    def __validar_preco(self, preco: Preco):
        if preco is not None and preco.precoLista is None and preco.precoDesconto is None:
            raise PrecoInvalido("Campos precoLista e precoDesconto são obrigatórios")
        if preco.precoLista < 0:
            raise PrecoInvalido("Campo precoLista não pode ser negativo")
        if preco.precoDesconto < 0:
            raise PrecoInvalido("Campo precoDesconto não pode ser negativo")
        if preco.precoDesconto > preco.precoLista:
            raise PrecoInvalido("Campo precoDesconto não pode ser maior que precoLista")
        
    def __validar_sku(self, sku: str):
        if sku is None or sku == "":
            raise SkuInvalido("Campo SKU é obrigatório")
        if sku is not None and len(sku) < 3:  
            raise SkuInvalido("Campo SKU deve ter no mínimo 3 caracteres")
        
    def __validar_produto(self, produto: Produto):
        self.__validar_sku(produto.sku)
        if produto.nome is None or produto.nome == "":
            raise ProdutoInvalido("Campo Nome é obrigatório")
        if produto.descr is None or produto.descr == "":
            raise ProdutoInvalido("Campo Descrição é obrigatório")
        if produto.urlImagem is not None and not produto.urlImagem.startswith("http://") and not produto.urlImagem.startswith("https://"):
                raise ProdutoInvalido("URL da imagem inválida")
        if produto.estoque:
            self.__validar_estoque(produto.estoque)
        if produto.preco:
            self.__validar_preco(produto.preco)
        
    def __validar_item_kit(self, item_kit: ItemKit):
        if item_kit is None or item_kit.qtd is None:
            raise ItemKitInvalido("Campo qtd é obrigatório")
        if item_kit.qtd < 1:
            raise ItemKitInvalido("Campo qtd não pode ser menor que 1")
        if item_kit.preco is None:
            raise ItemKitInvalido("Campo preco é obrigatório")
        self.__validar_preco(item_kit.preco)

    def __validar_produto_lista_item_kit(self, lista_item_kit: List[ItemKit]):
        for item_kit in lista_item_kit:
            if item_kit.kitId is not None and item_kit.kitId == item_kit.produtoId:
                raise ListaItemKitInvalida("Produto não pode ser um item de kit do próprio produto")
            
    def __validar_preco_lista_item_kit(self, lista_item_kit: List[ItemKit]):
        # Lógica para validação de preço total do kit    
        preco_lista_minimo = 15.0
        preco_desconto_minimo = 10.0
        preco_lista_total = 0
        preco_desconto_total = 0
        for item_kit in lista_item_kit:
            preco_lista_total += item_kit.preco.precoLista
            preco_desconto_total += item_kit.preco.precoDesconto
        if preco_lista_total < preco_lista_minimo:
            raise ListaItemKitInvalida(f"Preço total da lista deve ser maior que {preco_lista_minimo}")
        if preco_desconto_total < preco_desconto_minimo:
            raise ListaItemKitInvalida(f"Preço total do desconto deve ser maior que {preco_desconto_minimo}")
        
    def criar_produto(self, novo_produto: Produto):
        try:
            self.__validar_produto(novo_produto)
            self.__produto_repository.inserir(novo_produto, on_duplicate_sku=ProdutoJaExiste("Produto já existente"))
            self.__produto_event_publisher.publicar(novo_produto)
        except (SkuInvalido, PrecoInvalido, EstoqueInvalido, ProdutoInvalido, ProdutoJaExiste):
            raise
        except Exception as e:
            raise ErroAoCriarProduto(f"Erro ao criar produto: {e}")

    def obter_produto(self, sku: str) -> Produto:
        try:
            self.__validar_sku(sku)
            produto = self.__produto_repository.buscarPorSku(sku, on_not_found=ProdutoNaoEncontrado("Produto não encontrado"))
            if produto is None:
                raise ProdutoNaoEncontrado(f"Produto não encontrado")
            lista_item_kit = self.__produto_repository.busca_lista_item_kit(produto.id)
            produto.kit = lista_item_kit
            return produto
        except (SkuInvalido, ProdutoNaoEncontrado):
            raise
        except Exception as e:
            raise ErroAoObterProduto(f"Erro ao obter produto: {e}")

    def atualizar_produto(self, sku: str, produto: Produto):
        try:
            produto.sku = sku
            self.__validar_produto(produto)
            self.__produto_repository.atualizar(produto, on_not_found=ProdutoNaoEncontrado("Produto não encontrado"))
            self.__produto_event_publisher.publicar(produto)
        except (SkuInvalido, PrecoInvalido, EstoqueInvalido, ProdutoInvalido, ProdutoNaoEncontrado):
            raise
        except Exception as e:
            raise ErroAoAtualizarProduto(f"Erro ao atualizar produto: {e}")

    def deletar_produto(self, sku: str):
        try:
            self.__validar_sku(sku)
            self.__produto_repository.excluir(sku, on_not_found=ProdutoNaoEncontrado("Produto não encontrado"))
            return {"message": "Produto deletado com sucesso"}
        except (SkuInvalido, ProdutoNaoEncontrado):
            raise
        except Exception as e:
            raise ErroAoDeletarProduto(f"Erro ao deletar produto: {e}")
        
    def criar_item_kit(self, item_kit: ItemKit) -> ItemKit:
        try:
            if item_kit.produtoId is None:
                raise ItemKitInvalido("Campo produtoId é obrigatório")
            self.__validar_item_kit(item_kit)
            item_kit_id = self.__produto_repository.inserir_item_kit(item_kit, on_duplicate_id=ItemKitJaExiste("Item de kit já existente"), on_not_found=ProdutoNaoEncontrado("Produto não encontrado"))
            return self.__produto_repository.buscar_item_kit_por_id(item_kit_id, on_not_found=ItemKitNaoEncontrado("Item de kit não encontrado"))
        except (ItemKitInvalido, ItemKitNaoEncontrado, ItemKitJaExiste, PrecoInvalido, ProdutoNaoEncontrado):
            raise
        except Exception as e:
            raise ErroAoCriarItemKit(f"Erro ao criar item de kit: {e}")
    
    def atualizar_item_kit(self, id:int, item_kit: ItemKit):
        try:
            if id < 0:
                raise ItemKitInvalido("Id não pode ser negativo")
            item_kit.id = id
            self.__validar_item_kit(item_kit)
            item_kit_atual = self.__produto_repository.buscar_item_kit_por_id(id, on_not_found=ItemKitNaoEncontrado("Item de kit não encontrado"))
            
            if item_kit_atual.kitId is not None:        
                lista_item_kit = self.__produto_repository.busca_lista_item_kit(item_kit_atual.kitId)
                for item in lista_item_kit:
                    if item.id == item_kit_atual.id:
                        lista_item_kit.remove(item)
                        lista_item_kit.append(item_kit)
                        break
                if len(lista_item_kit) <= 0:
                    raise ErroListaInexistente("Lista de item kit inexistente")
                self.__validar_produto_lista_item_kit(lista_item_kit)
                self.__validar_preco_lista_item_kit(lista_item_kit)

            self.__produto_repository.atualizar_item_kit(item_kit, on_not_found=ProdutoNaoEncontrado("Produto não encontrado"), on_outdated_version=ItemKitInvalido("Item de kit desatualizado"))
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
        
    def vincular_lista_item_kit(self, sku: str, lista_item_kit: List[ItemKit]):
        try:
            self.__validar_sku(sku)
            produto = self.__produto_repository.buscarPorSku(sku, on_not_found=ProdutoNaoEncontrado("Produto não encontrado"))
            lista_item_kit_atual = []
            for item_kit in lista_item_kit:
                item_kit_atual = self.__produto_repository.buscar_item_kit_por_id(item_kit.id, on_not_found=ItemKitNaoEncontrado(f"Item de kit não encontrado: {item_kit.id}"))
                item_kit_atual.kitId = produto.id
                lista_item_kit_atual.append(item_kit_atual)
            self.__validar_produto_lista_item_kit(lista_item_kit_atual)
            if len(lista_item_kit_atual) > 0:
                self.__validar_preco_lista_item_kit(lista_item_kit_atual)
            self.__produto_repository.vincular_lista_item_kit(produto.id, lista_item_kit_atual, on_not_found=ProdutoNaoEncontrado("Produto Kit não encontrado"))
        except (ProdutoNaoEncontrado, SkuInvalido, ItemKitNaoEncontrado, ListaItemKitInvalida):
            raise
        except Exception as e:
            raise ErroAoVincularItemKit(f"Erro ao vincular item de kit: {e}")