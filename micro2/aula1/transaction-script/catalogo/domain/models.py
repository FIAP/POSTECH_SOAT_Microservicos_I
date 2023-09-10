from pydantic import BaseModel
from typing import Optional, List

class Estoque(BaseModel):
    id: Optional[int] = None
    emEstoque: int
    reservado: int = 0

class Preco(BaseModel):
    id: Optional[int] = None
    precoLista: float
    precoDesconto: float

class ItemKit(BaseModel):
    id: Optional[int] = None
    versao: Optional[int] = None
    kitId: Optional[int] = None
    produtoId: Optional[int] = None
    qtd: Optional[int] = None
    preco: Optional[Preco] = None

class Produto(BaseModel):
    id: Optional[int] = None
    versao: Optional[int] = None
    sku: Optional[str] = None
    nome: str
    descr: str
    urlImagem: Optional[str] = None
    preco: Optional[Preco] = None
    estoque: Optional[Estoque] = None
    kit: Optional[List[ItemKit]] = [] 