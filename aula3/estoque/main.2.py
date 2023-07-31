from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Table, MetaData, select, update, insert, Column, String, Float, Integer
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import sessionmaker, Session
from requests import post
import os
# Configuração do SQLAlchemy
DATABASE_URL = "mysql+mysqlconnector://user:password@db-estoque:3306/estoque"
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Criar tabela de estoque se não existir
estoque = Table(
   'estoque', metadata, 
   Column('sku', String(255), primary_key=True), 
   Column('em_estoque', Integer), 
   Column('reservado', Integer)
)
metadata.create_all(engine)

# Gerenciamento de sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()

def self_register():    
    url = "http://kong:8001/upstreams/estoque/targets"
    payload = {
        "target": os.environ['HOSTNAME'] + ":8080",
        "weight": 10,
        "tags": [ "estoque" ]
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    response = post(url, json=payload, headers=headers )
    return response

status_register = self_register()
print(status_register)

class NovoProduto(BaseModel):
    sku: str
    em_estoque: int
    reservado: int = 0

class Produto(BaseModel):
    em_estoque: int
    reservado: int = 0

class OperacaoEstoque(BaseModel):
    sku: str
    quantidade: int

class OperacoesEstoque(BaseModel):
    operacoes: List[OperacaoEstoque]

@app.post("/estoque")
async def criar_produto(produto: NovoProduto):
    # Criar uma nova sessão
    session = SessionLocal()
    try:
        insert_query = insert(estoque).values(
            sku=produto.sku,
            em_estoque=produto.em_estoque,
            reservado=produto.reservado)
        result = session.execute(insert_query)
        # Confirmar as mudanças
        session.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=400, detail="Erro ao registrar estoque do produto")
        return {"message": "Registro de estoque criado com sucesso"}
    except Exception as e:
        # Reverter as mudanças em caso de erro
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao registrar estoque do produto: {e}")
    finally:
        # Fechar a sessão
        session.close()

@app.get("/estoque/{sku}")
async def obter_estoque(sku: str):
    query = select(estoque).where(estoque.columns.sku == sku)
    with engine.connect() as connection:
        try:
            result = connection.execute(query).fetchone()
            if result is None:
                raise HTTPException(status_code=404, detail="Produto não encontrado")
            # Mapear valores para nomes de colunas
            column_names = [column.name for column in estoque.c]
            result_dict = dict(zip(column_names, result))
            return Produto(**result_dict)  # Passar o dicionário para Produto
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Produto não encontrado")

@app.put("/estoque/{sku}")
async def atualizar_produto(sku: str, produto: Produto):
    session = SessionLocal()
    try:
        update_query = update(estoque).where(estoque.columns.sku == sku).values(
            em_estoque=produto.em_estoque,
            reservado=produto.reservado)
        result = session.execute(update_query)
        session.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=400, detail="Erro ao atualizar estoque do produto")
        return {"message": "Registro de estoque atualizado com sucesso"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar estoque do produto: {e}")
    finally:
        session.close()

@app.post("/estoque/reserva")
async def reservar_estoque(operacoes: OperacoesEstoque):
    session = SessionLocal()
    try:
        for operacao in operacoes.operacoes:
            query = select(estoque).where(estoque.columns.sku == operacao.sku)
            produto = session.execute(query).fetchone()
            if operacao.quantidade > produto.em_estoque:
                raise HTTPException(status_code=400, detail=f"Estoque insuficiente para reserva do SKU {operacao.sku}")
            update_query = update(estoque).where(estoque.columns.sku == operacao.sku).values(
                em_estoque=produto.em_estoque - operacao.quantidade,
                reservado=produto.reservado + operacao.quantidade)
            session.execute(update_query)
        session.commit()
    except NoResultFound:
        session.rollback()
        raise HTTPException(status_code=404, detail=f"Produto com SKU {operacao.sku} não encontrado")
    finally:
        session.close()

@app.post("/estoque/debito")
async def debitar_estoque(operacoes: OperacoesEstoque):
    session = SessionLocal()
    try:
        for operacao in operacoes.operacoes:
            query = select(estoque).where(estoque.columns.sku == operacao.sku)
            produto = session.execute(query).fetchone()
            if operacao.quantidade > produto.reservado:
                raise HTTPException(status_code=400, detail=f"Estoque reservado insuficiente para debitar do SKU {operacao.sku}")
            update_query = update(estoque).where(estoque.columns.sku == operacao.sku).values(
                reservado=produto.reservado - operacao.quantidade)
            session.execute(update_query)
        session.commit()
    except NoResultFound:
        session.rollback()
        raise HTTPException(status_code=404, detail=f"Produto com SKU {operacao.sku} não encontrado")
    finally:
        session.close()

