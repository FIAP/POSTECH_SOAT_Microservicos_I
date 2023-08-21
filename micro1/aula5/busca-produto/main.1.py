from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from requests import get

app = FastAPI()

class Produto(BaseModel):
    sku: str
    nome: str
    descr: str
    urlImagem: str
    qtd:  Optional[int] = None
    preco: Optional[float] = None

@app.get("/produto/{sku}")
async def obter_produto(sku: str):
    catalogo = get(f"http://catalogo:8080/produto/{sku}").json()
    if catalogo.get("detail") is not None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    produto = {
        "sku": sku,
        "nome": catalogo["nome"],
        "descr": catalogo["descr"],
        "urlImagem": catalogo["urlImagem"],
        "qtd": None,
        "preco": None
    }

    preco = get(f"http://precificacao:8080/preco/{sku}").json()
    if preco.get("preco") is not None:
        produto["preco"] = preco["preco"]
    
    estoque = get(f"http://estoque:8080/estoque/{sku}").json()
    if estoque.get("em_estoque") is not None:
        produto["qtd"] = estoque["em_estoque"]

    return Produto(**produto)
