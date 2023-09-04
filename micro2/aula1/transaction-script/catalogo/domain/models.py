from pydantic import BaseModel
from typing import Optional

class Estoque(BaseModel):
    id: Optional[int] = None
    emEstoque: int
    reservado: int = 0

class Preco(BaseModel):
    id: Optional[int] = None
    precoLista: float
    precoDesconto: float

class Produto(BaseModel):
    id: Optional[int] = None
    sku: Optional[str] = None
    nome: str
    descr: str
    urlImagem: str
    preco: Optional[Preco] = None
    estoque: Optional[Estoque] = None