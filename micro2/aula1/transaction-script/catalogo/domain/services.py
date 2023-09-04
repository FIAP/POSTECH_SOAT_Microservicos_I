from domain.models import Produto, Preco, Estoque
from domain.exceptions import *
from port.repositories import ProdutoRepository
from port.event_publishers import ProdutoEventPublisher

class CatalogoService:
    def __init__(self, produto_repository: ProdutoRepository, produto_event_publisher: ProdutoEventPublisher):
        self.__produto_repository = produto_repository
        self.__produto_event_publisher = produto_event_publisher
    
    def __validar_estoque(self, estoque: Estoque):
        if estoque is not None and estoque.emEstoque is None:
            raise ProdutoInvalido("Campo emEstoque é obrigatório")
        if estoque.emEstoque < 0:
            raise ProdutoInvalido("Campo emEstoque não pode ser negativo")
        if estoque.reservado < 0:
            raise ProdutoInvalido("Campo reservado não pode ser negativo")
        
    def __validar_preco(self, preco: Preco):
        if preco is not None and preco.precoLista is None:
            raise ProdutoInvalido("Campo precoLista é obrigatório")
        if preco.precoLista < 0:
            raise ProdutoInvalido("Campo precoLista não pode ser negativo")
        if preco.precoDesconto < 0:
            raise ProdutoInvalido("Campo precoDesconto não pode ser negativo")
        if preco.precoDesconto > preco.precoLista:
            raise ProdutoInvalido("Campo precoDesconto não pode ser maior que precoLista")
        
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
        if not produto.urlImagem.startswith("http://") and not produto.urlImagem.startswith("https://"):
            raise ProdutoInvalido("URL da imagem inválida")
        if produto.estoque:
            self.__validar_estoque(produto.estoque)
        if produto.preco:
            self.__validar_preco(produto.preco)
        
    def criar_produto(self, novo_produto: Produto):
        try:
            produto = Produto(
                sku=novo_produto.sku,
                nome=novo_produto.nome,
                descr=novo_produto.descr,
                urlImagem=novo_produto.urlImagem,
                preco=Preco(
                    precoLista=novo_produto.preco.precoLista,
                    precoDesconto=novo_produto.preco.precoDesconto
                ) if novo_produto.preco else None,
                estoque=Estoque(
                    emEstoque=novo_produto.estoque.emEstoque,
                    reservado=novo_produto.estoque.reservado
                ) if novo_produto.estoque else None
            )
            self.__validar_produto(novo_produto)
            self.__produto_repository.inserir(novo_produto, on_duplicate_sku=ProdutoJaExiste("Produto já existente"))
            self.__produto_event_publisher.publicar(novo_produto)
        except (SkuInvalido, ProdutoInvalido, ProdutoJaExiste):
            raise
        except Exception as e:
            raise ErroAoCriarProduto(f"Erro ao criar produto: {e}")

    def obter_produto(self, sku: str) -> Produto:
        try:
            self.__validar_sku(sku)
            produto = self.__produto_repository.buscarPorSku(sku, on_not_found=ProdutoNaoEncontrado("Produto não encontrado"))
            if produto is None:
                raise ProdutoNaoEncontrado(f"Produto não encontrado")
            return produto
        except (SkuInvalido, ProdutoNaoEncontrado):
            raise
        except Exception as e:
            raise ProdutoNaoEncontrado(f"Produto não encontrado: {e}")

    def atualizar_produto(self, sku: str, produto: Produto):
        try:
            produto.sku = sku
            self.__validar_produto(produto)
            self.__produto_repository.atualizar(produto, on_not_found=ProdutoNaoEncontrado("Produto não encontrado"))
            self.__produto_event_publisher.publicar(produto)
        except (SkuInvalido, ProdutoInvalido, ProdutoNaoEncontrado):
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