from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Table, MetaData, select, update, insert, Column, String, Float, Integer
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import sessionmaker
import boto3

# Configuração do SQLAlchemy
DATABASE_URL = "mysql+mysqlconnector://precificacao_user:Mudar123!@db-servicos:3306/precificacao"
SQS_UPDATE_QUEUE = "preco-atualizacao"
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Criar tabela de preco se não existir
preco = Table(
   'preco', metadata, 
   Column('sku', String(255), primary_key=True), 
   Column('preco', Float)
)
metadata.create_all(engine)

# Gerenciamento de sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Inicializar cliente SQS
sqs = boto3.client('sqs', 
                   endpoint_url='http://localstack:4566', 
                   region_name='us-east-1',
                   aws_access_key_id='LKIAQBBBBBBBK7TDMD7S',
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

class Preco(BaseModel):
    sku: str
    preco: float

@app.post("/preco")
async def criar_preco(novo_preco: Preco):
    # Criar uma nova sessão
    session = SessionLocal()
    try:
        insert_query = insert(preco).values(
            sku=novo_preco.sku,
            preco=novo_preco.preco)
        result = session.execute(insert_query)
        # Confirmar as mudanças
        session.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=400, detail="Erro ao registrar preço do produto")
        
        send_to_sqs(SQS_UPDATE_QUEUE, novo_preco.json())

        return {"message": "Registro de preço criado com sucesso"}
    except Exception as e:
        # Reverter as mudanças em caso de erro
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao registrar preço do produto: {e}")
    finally:
        # Fechar a sessão
        session.close()

@app.get("/preco/{sku}")
async def obter_preco(sku: str):
    query = select(preco).where(preco.columns.sku == sku)
    with engine.connect() as connection:
        try:
            result = connection.execute(query).fetchone()
            if result is None:
                raise HTTPException(status_code=404, detail="Preco não encontrado")
            # Mapear valores para nomes de colunas
            column_names = [column.name for column in preco.c]
            result_dict = dict(zip(column_names, result))
            return Preco(**result_dict)  # Passar o dicionário para Preco
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Preco não encontrado")

@app.put("/preco/{sku}")
async def atualizar_preco(sku: str, atualiza_preco: Preco):
    session = SessionLocal()
    try:
        update_query = update(preco).where(preco.columns.sku == sku).values(
            preco=atualiza_preco.preco)
        result = session.execute(update_query)
        session.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=400, detail="Erro ao atualizar preço do produto")
        
        send_to_sqs(SQS_UPDATE_QUEUE, atualiza_preco.json())

        return {"message": "Registro de preço atualizado com sucesso"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar preço do produto: {e}")
    finally:
        session.close()

@app.delete("/preco/{sku}")
async def deletar_preco(sku: str):
    session = SessionLocal()
    try:
        delete_query = preco.delete().where(preco.columns.sku == sku)
        result = session.execute(delete_query)
        session.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=400, detail="Erro ao deletar preço do produto")
        return {"message": "Registro de preço deletado com sucesso"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao deletar preço do produto: {e}")
    finally:
        session.close()
        