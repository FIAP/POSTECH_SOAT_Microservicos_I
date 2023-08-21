from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import create_engine, Table, MetaData, select, update, Column, String, Float, Integer, Text
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.mysql import insert
import threading
import time
import boto3

app = FastAPI()

class Produto(BaseModel):
    sku: str
    nome: str
    descr: str
    urlImagem: str
    qtd: Optional[int] = None
    preco: Optional[float] = None

class CatalogoProduto(BaseModel):
    sku: str
    nome: str
    descr: str
    urlImagem: str

class Estoque(BaseModel):
    sku: str
    em_estoque: int
    reservado: int = 0

class Preco(BaseModel):
    sku: str
    preco: float

DATABASE_URL = "mysql+mysqlconnector://busca_produto_user:Mudar123!@db-servicos:3306/busca_produto"
engine = create_engine(DATABASE_URL)
metadata = MetaData()

produto = Table(
   'produto', metadata, 
   Column('sku', String(255), primary_key=True), 
   Column('nome', String(255)), 
   Column('descr', Text),
   Column('urlImagem', String(255)), 
   Column('qtd', Integer),
   Column('preco', Float)
)
metadata.create_all(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

sqs = boto3.client('sqs', 
                   endpoint_url='http://localstack:4566', 
                   region_name='us-east-1',
                   aws_access_key_id='LKIAQAAAAAAAK7TDMD7S',
                   aws_secret_access_key='6TfUN3ksRFSYv15hlPCtkNMLpzxHH5IVLBDu+E7V')
queues = {
    "estoque-atualizacao": "http://localstack:4566/000000000000/estoque-atualizacao",
    "preco-atualizacao": "http://localstack:4566/000000000000/preco-atualizacao",
    "produto-atualizacao": "http://localstack:4566/000000000000/produto-atualizacao"
}

def handle_sqs_message(queue_name, queue_url):
    while True:
        try:
            messages = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10)
            
            if 'Messages' in messages:
                for message in messages['Messages']:                    
                    # Processa a mensagem
                    process_message(message, queue_name)
                    # Deleta a mensagem da fila em caso de sucesso
                    sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=message['ReceiptHandle'])
            
            # Aguarda 5 segundos para a próxima obtenção de mensagens
            time.sleep(5)
        
        except Exception as e:
            print(f"Error processing message for queue {queue_name}: {str(e)}")
            time.sleep(10)


def process_message(message, queue_name):
    data = message['Body']
    session = SessionLocal()
    try:
        if queue_name == "produto-atualizacao":
            catalogo_data = CatalogoProduto.parse_raw(data)
            stmt = insert(produto).values(
                sku=catalogo_data.sku,
                nome=catalogo_data.nome,
                descr=catalogo_data.descr,
                urlImagem=catalogo_data.urlImagem
            ).on_duplicate_key_update(
                nome=catalogo_data.nome,
                descr=catalogo_data.descr,
                urlImagem=catalogo_data.urlImagem
            )
            session.execute(stmt)

        elif queue_name == "preco-atualizacao":
            preco_data = Preco.parse_raw(data)
            stmt = insert(produto).values(
                sku=preco_data.sku,
                preco=preco_data.preco
            ).on_duplicate_key_update(
                preco=preco_data.preco
            )
            session.execute(stmt)

        elif queue_name == "estoque-atualizacao":
            estoque_data = Estoque.parse_raw(data)
            stmt = insert(produto).values(
                sku=estoque_data.sku,
                qtd=estoque_data.em_estoque
            ).on_duplicate_key_update(
                qtd=estoque_data.em_estoque
            )
            session.execute(stmt)

        session.commit()

    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

@app.get("/produto/{sku}")
def obter_produto(sku: str):
    query = select(produto).where(produto.columns.sku == sku)
    with engine.connect() as connection:
        try:
            result = connection.execute(query).fetchone()
            if result is None :
                raise HTTPException(status_code=404, detail="Produto não encontrado")
            # Mapear valores para nomes de colunas
            column_names = [column.name for column in produto.c]
            result_dict = dict(zip(column_names, result))
            return Produto(**result_dict)  # Passar o dicionário para Produto
        except Exception as e:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        
@app.get("/produto")
def obter_produto(sku: Optional[str] = None, nome: Optional[str] = None, descr: Optional[str] = None):
    query = select(produto)
    if sku is None and nome is None and descr is None:
        raise HTTPException(status_code=400, detail="Informe ao menos um parâmetro de busca")
    if sku:
        query = query.where(produto.c.sku == sku)
    if nome:
        query = query.where(produto.c.nome.ilike(f'%{nome}%'))
    if descr:
        query = query.where(produto.c.descr.ilike(f'%{descr}%'))
    
    with engine.connect() as connection:
        try:
            result = connection.execute(query).fetchall()
            if result is None or len(result) == 0:
                raise HTTPException(status_code=204, detail="Produtos não encontrados na busca")
            # Mapear valores para nomes de colunas
            column_names = [column.name for column in produto.c]
            lista_produtos = []
            for row in result:
                result_dict = dict(zip(column_names, row))
                lista_produtos.append(Produto(**result_dict))
            return lista_produtos  # Passar o dicionário para Produto
        except NoResultFound:
            raise HTTPException(status_code=204, detail="Produtos não encontrados na busca")

@app.on_event("startup")
def start_sqs_handlers():
    for queue_name, queue_url in queues.items():
        threading.Thread(target=handle_sqs_message, args=(queue_name, queue_url)).start()
