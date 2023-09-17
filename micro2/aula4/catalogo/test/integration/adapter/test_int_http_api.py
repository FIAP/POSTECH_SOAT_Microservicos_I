from unittest import TestCase
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from adapter.http_api import HTTPAPIAdapter
from domain.exceptions import ProdutoJaExiste

class TestIntegrationHTTPAPIAdapter(TestCase):
    
    def setUp(self):
        self.catalogoService = Mock()
        self.httpAdapter = HTTPAPIAdapter(catalogo_service=self.catalogoService)
        self.app = FastAPI()
        self.app.include_router(self.httpAdapter.router)
        self.client = TestClient(self.app)
        
    def testCriarProdutoComSucesso(self):
        request_data = {
            "sku": "SKU123",
            "nome": "Produto Teste",
            "descr": "Descrição Teste",
            "urlImagem": "http://imagem",
            "estoque": {
                "emEstoque": 10,
                "reservado": 0
            },
            "preco": {
                "precoLista": 20.0,
                "precoDesconto": 15.0
            }
        }
        
        response = self.client.post("/produto", json=request_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Produto criado com sucesso"})
        self.catalogoService.criar_produto.assert_called()
        
    def testCriarProdutoFalhaProdutoJaExiste(self):
        self.catalogoService.criar_produto.side_effect = ProdutoJaExiste("Produto já existente")
        
        request_data = {
            "sku": "SKU123",
            "nome": "Produto Teste",
            "descr": "Descrição Teste",
            "urlImagem": "http://imagem",
            "estoque": {
                "emEstoque": 10,
                "reservado": 0
            },
            "preco": {
                "precoLista": 20.0,
                "precoDesconto": 15.0
            }
        }
        
        response = self.client.post("/produto", json=request_data)
        
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), {"detail": "Erro ao criar produto: Produto já existente"})
