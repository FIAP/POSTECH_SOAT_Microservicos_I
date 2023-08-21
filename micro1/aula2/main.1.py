from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

class Produto(BaseModel):
    em_estoque: int
    reservado: int = 0

class OperacaoEstoque(BaseModel):
    sku: str
    quantidade: int

class OperacoesEstoque(BaseModel):
    operacoes: List[OperacaoEstoque]

estoque = {
    "123": Produto(em_estoque=10),
    "456": Produto(em_estoque=5),
    "789": Produto(em_estoque=2)
}

@app.get("/estoque/{sku}")
async def obter_estoque(sku: str):
    produto = estoque.get(sku)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto

@app.post("/estoque/reserva")
async def reservar_estoque(operacoes: OperacoesEstoque):
    for operacao in operacoes.operacoes:
        produto = estoque.get(operacao.sku)
        if not produto:
            raise HTTPException(status_code=404, detail=f"Produto com SKU {operacao.sku} não encontrado")
        if operacao.quantidade > produto.em_estoque:
            raise HTTPException(status_code=400, detail=f"Estoque insuficiente para reserva do SKU {operacao.sku}")
        produto.em_estoque -= operacao.quantidade
        produto.reservado += operacao.quantidade
    return operacoes

@app.post("/estoque/debito")
async def debitar_estoque(operacoes: OperacoesEstoque):
    for operacao in operacoes.operacoes:
        produto = estoque.get(operacao.sku)
        if not produto:
            raise HTTPException(status_code=404, detail=f"Produto com SKU {operacao.sku} não encontrado")
        if operacao.quantidade > produto.reservado:
            raise HTTPException(status_code=400, detail=f"Estoque reservado insuficiente para debitar do SKU {operacao.sku}")
        produto.reservado -= operacao.quantidade
    return operacoes
