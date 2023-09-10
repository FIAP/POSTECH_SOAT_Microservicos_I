from fastapi import FastAPI
from adapter.http_api import HTTPAPIAdapter
from domain.services import CatalogoService
from adapter.mysql_adapter import ProdutoMySQLAdapter
from adapter.sqs_adapter import SQSAdapter

DATABASE_URL = "mysql+mysqlconnector://catalogo_user:Mudar123!@db-servicos:3306/catalogo"
QUEUE_NAME = "produto-atualizacao"
ENDPOINT_URL='http://localstack:4566'
REGION_NAME='us-east-1'
AWS_ACCESS_KEY_ID='LKIAQAAAAAAAFFCVQQVU'
AWS_SECRET_ACCESS_KEY='wEWEKcBy8wQDOp5STKPfUUS/wykE6er26Taj/YFP'

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    produto_mysql_adapter = ProdutoMySQLAdapter(DATABASE_URL)
    sqs_adapter = SQSAdapter(QUEUE_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, ENDPOINT_URL, REGION_NAME)
    catalogo_service = CatalogoService(produto_mysql_adapter, sqs_adapter)
    http_api_adapter = HTTPAPIAdapter(catalogo_service)
    app.include_router(http_api_adapter.router)