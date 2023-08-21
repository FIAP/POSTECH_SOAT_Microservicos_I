from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Table, MetaData, select, update, insert, Column, String, Float, Integer, Text
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import sessionmaker
import boto3

# Configuração do SQLAlchemy
DATABASE_URL = "mysql+mysqlconnector://catalogo_user:Mudar123!@db-servicos:3306/catalogo"
SQS_UPDATE_QUEUE = "produto-atualizacao"
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Criar tabela de estoque se não existir
produto = Table(
   'produto', metadata, 
   Column('sku', String(255), primary_key=True), 
   Column('nome', String(255)), 
   Column('descr', Text),
   Column('urlImagem', String(255)), 
)
metadata.create_all(engine)

# Gerenciamento de sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Inicializar cliente SQS
sqs = boto3.client('sqs', 
                   endpoint_url='http://localstack:4566', 
                   region_name='us-east-1',
                   aws_access_key_id='LKIAQCCCCCCCK7TDMD7S',
                   aws_secret_access_key='6TfUN3ksRFSYv15hlPCtkNMLpzxHH5IVLBDu+E7V')

def send_to_sqs(queue_name: str, message_body: str):
    try:
        # Get the URL for the queue
        response = sqs.get_queue_url(QueueName=queue_name)
        queue_url = response['QueueUrl']
        
        # Send the message
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=message_body
        )
    except Exception as e:
        print(f"Error sending message to SQS: {e}")


app = FastAPI()

class Produto(BaseModel):
    sku: str
    nome: str
    descr: str
    urlImagem: str

@app.post("/produto")
async def criar_produto(novo_produto: Produto):
    # Criar uma nova sessão
    session = SessionLocal()
    try:
        insert_query = insert(produto).values(
            sku=novo_produto.sku,
            nome=novo_produto.nome,
            descr=novo_produto.descr,
            urlImagem=novo_produto.urlImagem)
        result = session.execute(insert_query)
        # Confirmar as mudanças
        session.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=400, detail="Erro ao registrar produto")
        
        send_to_sqs(SQS_UPDATE_QUEUE, novo_produto.json())

        return {"message": "Produto criado com sucesso"}
    except Exception as e:
        # Reverter as mudanças em caso de erro
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao registrar produto: {e}")
    finally:
        # Fechar a sessão
        session.close()

@app.get("/produto/{sku}")
async def obter_produto(sku: str):
    query = select(produto).where(produto.columns.sku == sku)
    with engine.connect() as connection:
        try:
            result = connection.execute(query).fetchone()
            if result is None:
                raise HTTPException(status_code=404, detail="Produto não encontrado")
            # Mapear valores para nomes de colunas
            column_names = [column.name for column in produto.c]
            result_dict = dict(zip(column_names, result))
            return Produto(**result_dict)  # Passar o dicionário para Produto
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Produto não encontrado")

@app.put("/produto/{sku}")
async def atualizar_produto(sku: str, atualiza_produto: Produto):
    session = SessionLocal()
    try:
        update_query = update(produto).where(produto.columns.sku == sku).values(
            nome=atualiza_produto.nome,
            descr=atualiza_produto.descr,
            urlImagem=atualiza_produto.urlImagem)
        result = session.execute(update_query)
        session.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=400, detail="Erro ao atualizar produto")
        
        send_to_sqs(SQS_UPDATE_QUEUE, atualiza_produto.json())

        return {"message": "Produto atualizado com sucesso"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar produto: {e}")
    finally:
        session.close()

@app.delete("/produto/{sku}")
async def deletar_produto(sku: str):
    session = SessionLocal()
    try:
        delete_query = produto.delete().where(produto.columns.sku == sku)
        result = session.execute(delete_query)
        session.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=400, detail="Erro ao deletar produto")
        return {"message": "Produto deletado com sucesso"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao deletar produto: {e}")
    finally:
        session.close()