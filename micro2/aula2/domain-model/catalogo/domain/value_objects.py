from pydantic import BaseModel, validator, PrivateAttr
from domain.exceptions import *
from typing import Optional


class Estoque:
    def __init__(self, emEstoque: int, reservado: int = 0, id: Optional[int] = None):
        self._id = id
        self._emEstoque = self._validarEmEstoque(emEstoque)
        self._reservado = self._validarReservado(reservado)

    @staticmethod
    def _validarEmEstoque(emEstoque: int) -> int:
        if emEstoque is None:
            raise EstoqueInvalido("Campo emEstoque é obrigatório")
        if emEstoque < 0:
            raise EstoqueInvalido("Campo emEstoque não pode ser negativo")
        return emEstoque

    @staticmethod
    def _validarReservado(reservado: int) -> int:
        if reservado is None:
            raise EstoqueInvalido("Campo reservado é obrigatório")
        if reservado < 0:
            raise EstoqueInvalido("Campo reservado não pode ser negativo")
        return reservado

    @property
    def id(self) -> Optional[int]:
        return self._id

    @property
    def emEstoque(self) -> int:
        return self._emEstoque

    @property
    def reservado(self) -> int:
        return self._reservado

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "emEstoque": self.emEstoque,
            "reservado": self.reservado
        }

class Preco:
    def __init__(self, precoLista: float, precoDesconto: float, id: Optional[int] = None):
        self._id = id
        self._validarPrecoLista(precoLista)
        self._validarPrecoDesconto(precoDesconto, precoLista)
        self._precoLista = precoLista
        self._precoDesconto = precoDesconto

    @staticmethod
    def _validarPrecoLista(precoLista: float):
        if precoLista is None:
            raise PrecoInvalido("Campo precoLista é obrigatório")
        if precoLista < 0:
            raise PrecoInvalido("Campo precoLista não pode ser negativo")

    @staticmethod
    def _validarPrecoDesconto(precoDesconto: float, precoLista: float):
        if precoDesconto is None:
            raise PrecoInvalido("Campo precoDesconto é obrigatório")
        if precoDesconto < 0:
            raise PrecoInvalido("Campo precoDesconto não pode ser negativo")
        if precoDesconto > precoLista:
            raise PrecoInvalido("Campo precoDesconto não pode ser maior que precoLista")

    @property
    def id(self) -> Optional[int]:
        return self._id

    @property
    def precoLista(self) -> float:
        return self._precoLista

    @property
    def precoDesconto(self) -> float:
        return self._precoDesconto

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "precoLista": self.precoLista,
            "precoDesconto": self.precoDesconto
        }

class ItemKitDetalhe:
    def __init__(self, qtd: Optional[int] = None, preco: Optional['Preco'] = None):
        self._validarQtd(qtd)
        self._validarPreco(preco)
        self._qtd = qtd
        self._preco = preco

    @staticmethod
    def _validarQtd(qtd: Optional[int]):
        if qtd is None:
            raise ItemKitInvalido("Campo qtd é obrigatório")
        if qtd < 1:
            raise ItemKitInvalido("Campo qtd não pode ser menor que 1")

    @staticmethod
    def _validarPreco(preco: Optional['Preco']):
        if preco is None:
            raise PrecoInvalido("Campo preco é obrigatório")

    @property
    def qtd(self) -> Optional[int]:
        return self._qtd

    @property
    def preco(self) -> Optional['Preco']:
        return self._preco

    def to_dict(self) -> dict:
        return {
            "qtd": self.qtd,
            "preco": self.preco.to_dict()
        }