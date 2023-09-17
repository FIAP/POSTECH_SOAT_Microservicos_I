from fastapi import FastAPI
from adapter.http_api import HTTPAPIAdapter
from adapter.mysql_adapter import ProdutoMySQLAdapter
from adapter.sqs_adapter import SQSAdapter
from domain.services import CatalogoService
from domain.entities import Produto
from domain.exceptions import ProdutoJaExiste
from domain.value_objects import Preco, Estoque
from sqlalchemy import create_engine
import threading
from uvicorn import Config, Server
import requests
import boto3
import re
import os
import requests
import json
import os
import pytest
from unidecode import unidecode

class TestComponentCatalogo:  
    @staticmethod
    def loadInteractions():
        # Carregar dinamicamente os arquivos de contrato. 
        # Cada arquivo é um contrato, que representa uma suite de testes de um consumer
        contractsDir = './test/component/contracts/'
        contractFiles = [f for f in os.listdir(contractsDir) if f.endswith('.json')]
        contracts = {}
        for contractFile in contractFiles:
            with open(os.path.join(contractsDir, contractFile), 'r') as f:
                contracts[contractFile] = json.load(f)

        # Extrair as interações de cada contrato. Cada interação é um teste
        interactionIds = []
        interactions = []
        for contractName, contract in contracts.items():
            for interaction in contract['interactions']:
                interactionIds.append(f"{contractName} - {unidecode(interaction['description'])}")
                interactions.append((contractName, interaction))
        return interactions, interactionIds

    # Carregar as interações de teste
    interactions, interactionIds = loadInteractions.__func__()

    # Configuração do ambiente de teste
    def setUp(self):
        DATABASE_URL = "mysql+mysqlconnector://catalogo_user:Mudar123!@test-db-catalogo:3306/catalogo"
        self.queueName = "produto-atualizacao"
        ENDPOINT_URL='http://localstack:4566'
        REGION_NAME='us-east-1'
        AWS_ACCESS_KEY_ID='LKIAQAAAAAAAFFCVQQVU'
        AWS_SECRET_ACCESS_KEY='wEWEKcBy8wQDOp5STKPfUUS/wykE6er26Taj/YFP'

        self.engine = create_engine(DATABASE_URL)
        self.sqs = boto3.client('sqs', region_name=REGION_NAME,
                               endpoint_url=ENDPOINT_URL,
                               aws_access_key_id=AWS_ACCESS_KEY_ID,
                               aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        
        self.produtoMysqlAdapter = ProdutoMySQLAdapter(DATABASE_URL)
        self.sqsAdapter = SQSAdapter(self.queueName, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, ENDPOINT_URL, REGION_NAME)
        self.catalogoService = CatalogoService(self.produtoMysqlAdapter, self.sqsAdapter)
        self.httpAdapter = HTTPAPIAdapter(self.catalogoService)
        self.app = FastAPI()
        self.app.include_router(self.httpAdapter.router)
        config = Config(app=self.app, host="0.0.0.0", port=8080, loop="asyncio")
        self.server = Server(config=config)
        
        # Iniciar o servidor FastAPI em uma nova thread
        self.thread = threading.Thread(target=self.server.run)
        self.thread.start()
        #----------------------------
        self.produtoMysqlAdapter._ProdutoMySQLAdapter__metadata.drop_all(self.engine)
        self.produtoMysqlAdapter._ProdutoMySQLAdapter__metadata.create_all(self.engine)
        # Criar uma nova fila
        response = self.sqs.create_queue(
            QueueName=self.queueName,
            Attributes={
                'DelaySeconds': '0',
                'MessageRetentionPeriod': '86400'
            }
        )
        self.queueUrl = response['QueueUrl']
        
    def tearDown(self):
        self.produtoMysqlAdapter._ProdutoMySQLAdapter__metadata.drop_all(self.engine)
        self.sqs.delete_queue(QueueUrl=self.queueUrl)
        self.server.should_exit = True # Sinalizar para o servidor parar
        self.thread.join() # Aguardar a thread terminar

    # Configuração do estado do mock de CatalogoService
    def setCatalogoState(self, providerState):
        if re.match(r"^Um produto já cadastrado @sku=(\w+)$", providerState):
            sku = re.match(r"^Um produto já cadastrado @sku=(\w+)$", providerState).group(1)
            # produto = Produto(
            self.produtoMysqlAdapter.inserir(
                Produto(
                    sku=sku,
                    nome="Produto Teste",
                    descr="Descrição Teste",
                    urlImagem="http://imagem",
                    preco=Preco(10.0, 5.0),
                    estoque=Estoque(10, 0)
                ), 
                on_duplicate_sku=ProdutoJaExiste("Produto já existente")
            )

    # Executa cada interação de teste com pytest
    @pytest.mark.parametrize("interactionData", interactions, ids=interactionIds)
    def testComponent(self, interactionData):
        self.setUp()
        contractName, interaction = interactionData

        req = interaction['request']
        respExpected = interaction['response']

        # Configurar o estado do serviço para cada interação
        providerState = interaction.get('providerState')
        self.setCatalogoState(providerState)

        # Executar a requisição usando o FastAPI TestClient
        baseUrl = 'http://localhost:8080'
        if req['method'] == 'GET':
            response = requests.get(baseUrl+req['path'], headers=req['headers'])
        elif req['method'] == 'POST':
            response = requests.post(baseUrl+req['path'], json=req['body'], headers=req['headers'])
        elif req['method'] == 'PUT':
            response = requests.put(baseUrl+req['path'], json=req['body'], headers=req['headers'])
        elif req['method'] == 'DELETE':
            response = requests.delete(baseUrl+req['path'], headers=req['headers'])

        # Verificar o status_code e o body
        assert response.status_code == respExpected['status']
        if respExpected.get('body'):
            assert response.json() == respExpected['body']
        if respExpected.get('headers'):
            assert response.headers == respExpected['headers']
        
        self.tearDown()
