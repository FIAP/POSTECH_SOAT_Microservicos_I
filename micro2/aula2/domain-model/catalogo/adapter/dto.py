from pydantic import BaseModel
from typing import Optional, List

class EstoqueDTO(BaseModel):
    emEstoque: int
    reservado: Optional[int] = 0

class PrecoDTO(BaseModel):
    precoLista: float
    precoDesconto: float

class ItemKitDTO(BaseModel):
    produtoId: int
    qtd: int
    preco: PrecoDTO

class ItemKitRequestDTO(BaseModel):
    produtoId: int
    qtd: int
    preco: PrecoDTO

class ItemKitDetalheRequestDTO(BaseModel):
    qtd: int
    preco: PrecoDTO

class ItemKitResponseDTO(BaseModel):
    id: int
    kitId: Optional[int] = None
    produtoId: int
    qtd: int
    preco: PrecoDTO

class ProdutoRequestDTO(BaseModel):
    sku: str
    nome: str
    descr: str
    urlImagem: Optional[str] = None
    preco: Optional[PrecoDTO] = None
    estoque: Optional[EstoqueDTO] = None

class ProdutoResponseDTO(BaseModel):
    id: int
    sku: str
    nome: str
    descr: str
    urlImagem: Optional[str] = None
    preco: Optional[PrecoDTO] = None
    estoque: Optional[EstoqueDTO] = None
    kit: Optional[List[ItemKitDTO]] = []