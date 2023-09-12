from pydantic import BaseModel, validator
from domain.value_objects import Estoque, Preco, ItemKitDetalhe
from domain.exceptions import *
from typing import Optional, List, ForwardRef

ItemKitRef = ForwardRef('ItemKit')

class ItemKit:
    def __init__(self, qtd: Optional[int] = None, preco: Optional[Preco] = None, 
                 id: Optional[int] = None, versao: Optional[int] = None, 
                 kitId: Optional[int] = None, produtoId: Optional[int] = None, **kwargs):
          
        self._id = id
        self._versao = versao
        self._kitId = kitId
        self._produtoId = produtoId
        self._qtd = qtd
        self._preco = preco

        self.validarProdutoId()
        self.validarKitId(kitId)

    def validarProdutoId(self):
        if self._produtoId is None:
            raise ItemKitInvalido("Produto não pode ser um item de kit sem produto")

    def validarKitId(self, kitId: int):
        if self._produtoId == kitId:
            raise ItemKitInvalido("Produto não pode ser um item de kit do próprio produto")

    @staticmethod
    def validarProdutoListaItemKit(listaItemKit: List[ItemKitRef]):
        for itemKit in listaItemKit:
            if itemKit.kitId is not None and itemKit.kitId == itemKit.produtoId:
                raise ListaItemKitInvalida("Produto não pode ser um item de kit do próprio produto")
    
    @staticmethod
    def validarPrecoListaItemKit(listaItemKit: List[ItemKitRef]):
        # Lógica para validação de preço total do kit
        if listaItemKit is None or len(listaItemKit) == 0:
            return
        precoListaMinimo = 15.0
        precoDescontoMinimo = 10.0
        precoListaTotal = 0
        precoDescontoTotal = 0
        for itemKit in listaItemKit:
            precoListaTotal += itemKit.preco.precoLista
            precoDescontoTotal += itemKit.preco.precoDesconto
        if precoListaTotal < precoListaMinimo:
            raise ListaItemKitInvalida(f"Preço total da lista deve ser maior que {precoListaMinimo}")
        if precoDescontoTotal < precoDescontoMinimo:
            raise ListaItemKitInvalida(f"Preço total do desconto deve ser maior que {precoDescontoMinimo}")

    @staticmethod
    def vincularProduto(listaItemKit: List[ItemKitRef]):
        if listaItemKit is None or len(listaItemKit) == 0:
            return
        ItemKit.validarProdutoListaItemKit(listaItemKit)
        ItemKit.validarPrecoListaItemKit(listaItemKit)

    def atualizar(self, itemKit: ItemKitDetalhe):
        self._qtd = itemKit.qtd
        self._preco = itemKit.preco
    
    @property
    def id(self) -> Optional[int]:
        return self._id

    @property
    def versao(self) -> Optional[int]:
        return self._versao

    @property
    def kitId(self) -> Optional[int]:
        return self._kitId

    @property
    def produtoId(self) -> Optional[int]:
        return self._produtoId

    @property
    def qtd(self) -> Optional[int]:
        return self._qtd

    @property
    def preco(self) -> Optional[Preco]:
        return self._preco

    def setKitId(self, kitId: int):
        self.validarKitId(kitId)       
        self._kitId = kitId
        
    def to_dict(self):
        return {
            "id": self.id,
            "versao": self.versao,
            "kitId": self.kitId,
            "produtoId": self.produtoId,
            "qtd": self.qtd,
            "preco": self.preco.to_dict() if self.preco is not None else None
        }

class Produto:
    def __init__(self, nome: str, descr: str, urlImagem: str, 
                 id: Optional[int] = None, versao: Optional[int] = None, 
                 sku: Optional[str] = None, preco: Optional[Preco] = None, 
                 estoque: Optional[Estoque] = None, kit: Optional[List['ItemKit']] = None, **kwargs):
        
        self.validarSku(sku)
        self.validarNome(nome)
        self.validarDescr(descr)
        self.validarUrlImagem(urlImagem)

        if kit is not None:
            for itemKit in kit:
                itemKit.setKitId(id)
            self.validarKit(kit)
            
        self._id = id
        self._versao = versao
        self._sku = sku
        self._nome = nome
        self._descr = descr
        self._urlImagem = urlImagem
        self._preco = preco
        self._estoque = estoque
        self._kit = kit if kit is not None else []

    @staticmethod
    def validarSku(sku: str):
        if sku is None or sku == "":
            raise SkuInvalido("Campo SKU é obrigatório")
        if len(sku) < 3:
            raise SkuInvalido("Campo SKU deve ter no mínimo 3 caracteres")

    @staticmethod
    def validarNome(nome: str):
        if nome is None or nome == "":
            raise ProdutoInvalido("Campo nome é obrigatório")
        if len(nome) < 3:
            raise ProdutoInvalido("Campo nome deve ter no mínimo 3 caracteres")

    @staticmethod
    def validarDescr(descr: str):
        if descr is None or descr == "":
            raise ProdutoInvalido("Campo descr é obrigatório")
        if len(descr) < 3:
            raise ProdutoInvalido("Campo descr deve ter no mínimo 3 caracteres")

    @staticmethod
    def validarUrlImagem(urlImagem: str):
        if not urlImagem.startswith("http://") and not urlImagem.startswith("https://"):
            raise ProdutoInvalido("URL da imagem inválida")

    @property
    def id(self) -> Optional[int]:
        return self._id

    @property
    def versao(self) -> Optional[int]:
        return self._versao

    @property
    def sku(self) -> Optional[str]:
        return self._sku

    @property
    def nome(self) -> str:
        return self._nome

    @property
    def descr(self) -> str:
        return self._descr

    @property
    def urlImagem(self) -> str:
        return self._urlImagem

    @property
    def preco(self) -> Optional[Preco]:
        return self._preco

    @property
    def estoque(self) -> Optional[Estoque]:
        return self._estoque

    @property
    def kit(self) -> List['ItemKit']:
        return self._kit

    def to_dict(self):
        return {
            "id": self.id,
            "versao": self.versao,
            "sku": self.sku,
            "nome": self.nome,
            "descr": self.descr,
            "urlImagem": self.urlImagem,
            "preco": self.preco.to_dict() if self.preco is not None else None,
            "estoque": self.estoque.to_dict() if self.estoque is not None else None,
            "kit": [itemKit.to_dict() for itemKit in self.kit]
        }
    
    def setKit(self, kit: List['ItemKit']):
        for itemKit in kit:
            itemKit.setKitId(self.id)
        self.validarKit(kit)
        self._kit = kit

    @staticmethod
    def validarKit(kit: List['ItemKit']):
        if kit is None or len(kit) == 0:
            return
        ItemKit.validarProdutoListaItemKit(kit)
        ItemKit.validarPrecoListaItemKit(kit)

    def inserirListaItemKit(self, listaItemKitDetalhe: List['ItemKitDetalhe']):
        if len(listaItemKitDetalhe) == 0:
            raise ListaItemKitInvalida("Lista de item de kit não pode ser vazia")
        kit = self._kit.copy()
        for item in kit:
            if item.produtoId in [itemKit.produtoId for itemKit in listaItemKitDetalhe]:
                raise ItemKitInvalido(f"Produto com produtoId {item.produtoId} já está no kit")
        for itemKitDetalhe in listaItemKitDetalhe:
            itemKit = ItemKit(kitId=self.id, qtd=itemKitDetalhe.qtd, preco=itemKitDetalhe.preco, produtoId=itemKitDetalhe.produtoId)
            kit.append(itemKit)
        self.validarKit(kit)
        self._kit = kit

    def atualizarItemKit(self, produtoId: int, qtd: int, preco: Preco):
        kit = self._kit.copy()
        atualizado = False
        for item in kit:
            if item.produtoId == produtoId:
                itemKitDetalhe = ItemKitDetalhe(qtd=qtd, preco=preco)
                item.atualizar(itemKitDetalhe)
                atualizado = True
                break
        if not atualizado:
            raise ItemKitNaoEncontrado(f"Item de kit com produtoId {produtoId} não encontrado")
        self.validarKit(kit)
        self._kit = kit

    def removerItemKit(self, produtoId: int):
        kit = self._kit.copy()
        deletado = False
        for item in kit:
            if item.produtoId == produtoId:
                kit.remove(item)
                deletado = True
                break
        if not deletado:
            raise ItemKitNaoEncontrado(f"Item de kit com produtoId {produtoId} não encontrado")
        self.validarKit(kit)
        self._kit = kit

    def obterItemKit(self, produtoId: int) -> Optional[ItemKit]:
        for item in self._kit:
            if item.produtoId == produtoId:
                return item
        raise ItemKitNaoEncontrado(f"Item de kit não encontrado")