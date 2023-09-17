import json
import os
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from adapter.http_api import HTTPAPIAdapter
from domain.exceptions import *
from unidecode import unidecode

class TestIntegrationContract:

    @staticmethod
    def carregarInteractions():
        # Carrega dinamicamente os arquivos de contrato. 
        # Cada arquivo é um contrato, que representa uma suite de testes de um consumer
        contractsDir = './test/integration/contracts/'
        contractFiles = [f for f in os.listdir(contractsDir) if f.endswith('.json')]
        contracts = {}
        for contractFile in contractFiles:
            with open(os.path.join(contractsDir, contractFile), 'r') as f:
                contracts[contractFile] = json.load(f)

        # Extrai as interações de cada contrato. Cada interação é um teste
        interactionIds = []
        interactions = []
        for contractName, contract in contracts.items():
            for interaction in contract['interactions']:
                interactionIds.append(f"{contractName} - {unidecode(interaction['description'])}")
                interactions.append((contractName, interaction))
        return interactions, interactionIds

    # Carrega as interações de teste
    interactions, interactionIds = carregarInteractions.__func__()
    
    # Configuração do ambiente de teste
    def setUpClass(self):
        self.catalogoService = Mock()
        self.httpAdapter = HTTPAPIAdapter(catalogo_service=self.catalogoService)
        self.app = FastAPI()
        self.app.include_router(self.httpAdapter.router)
        self.client = TestClient(self.app)
    
    # Configuração do estado do mock de CatalogoService
    def setCatalogoState(self, catalogoService, provider_state):
        if provider_state == 'SKU Inválido':
            catalogoService.criar_produto.side_effect = SkuInvalido("SKU inválido")
        elif provider_state == 'Um produto já existente':
            catalogoService.criar_produto.side_effect = ProdutoJaExiste("Produto já existente")
        else:
            catalogoService.criar_produto.side_effect = None

    # Configuração do estado do mock de Estoque
    def setEstoqueState(self, estoque, provider_state):
        if provider_state == "Um produto com estoque inválido":
            estoque.side_effect = EstoqueInvalido("Estoque inválido")
        else:
            estoque.side_effect = None

    # Configuração do estado do mock de Preco
    def setPrecoState(self, preco, provider_state):
        if provider_state == "Um produto com preço de desconto maior que o preço de lista":
            preco.side_effect = PrecoInvalido("Campo precoDesconto não pode ser maior que precoLista")
        else:
            preco.side_effect = None
    
    # Executa cada interação de teste com pytest
    configurado = False
    
    @pytest.mark.parametrize("interactionData", interactions, ids=interactionIds)
    @patch('adapter.http_api.Preco')
    @patch('adapter.http_api.Estoque')
    def testContract(self, MockedEstoque, MockedPreco, interactionData):
        if not self.configurado:
            self.setUpClass()
            self.configurado = True
            
        contractName, interaction = interactionData

        req = interaction['request']
        respExpected = interaction['response']

        # Configura cada mock conforme estado do provedor
        providerState = interaction.get('providerState')
        self.setCatalogoState(self.catalogoService, providerState)
        self.setEstoqueState(MockedEstoque, providerState)
        self.setPrecoState(MockedPreco, providerState)

        # Executa a requisição usando o FastAPI TestClient       
        if req['method'] == 'GET':
            response = self.client.get(req['path'], headers=req['headers'])
        elif req['method'] == 'POST':
            response = self.client.post(req['path'], json=req['body'], headers=req['headers'])
        elif req['method'] == 'PUT':
            response = self.client.put(req['path'], json=req['body'], headers=req['headers'])
        elif req['method'] == 'DELETE':
            response = self.client.delete(req['path'], headers=req['headers'])

        # Verificar o status_code e o body
        assert response.status_code == respExpected['status']
        if respExpected.get('body'):
            assert response.json() == respExpected['body']
        if respExpected.get('headers'):
            assert response.headers == respExpected['headers']