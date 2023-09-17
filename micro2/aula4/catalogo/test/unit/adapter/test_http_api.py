from unittest import TestCase
from unittest.mock import patch, Mock
from adapter.http_api import HTTPAPIAdapter
from domain.exceptions import SkuInvalido
from fastapi import HTTPException
import pytest

class TestHTTPAPIAdapter(TestCase):
    
    def setUp(self):
        self.catalogoService = Mock()
        self.httpAdapter = HTTPAPIAdapter(catalogo_service=self.catalogoService)
        
    @patch('adapter.http_api.EstoqueDTO')
    @patch('adapter.http_api.PrecoDTO')
    @patch('adapter.http_api.Preco')
    @patch('adapter.http_api.Estoque')
    @patch('adapter.http_api.ProdutoRequestDTO')
    def testCriarProdutoComSucesso(self, MockProdutoRequestDTO, MockEstoque, MockPreco, MockPrecoDTO, MockEstoqueDTO):
        mockProdutoRequestDTO = Mock()
        mockEstoque = Mock()
        mockPreco = Mock()
        mockEstoqueDTO = Mock()
        mockPrecoDTO = Mock()
        
        mockEstoqueDTO.emEstoque = 10
        mockPrecoDTO.precoLista = 10.0
        mockPrecoDTO.precoDesconto = 9.0
        
        mockProdutoRequestDTO.sku = "123"
        mockProdutoRequestDTO.nome = "Produto Teste"
        mockProdutoRequestDTO.descr = "Descrição Teste"
        mockProdutoRequestDTO.urlImagem = "http://imagem"
        mockProdutoRequestDTO.estoque = mockEstoqueDTO
        mockProdutoRequestDTO.preco = mockPrecoDTO

        MockProdutoRequestDTO.return_value = mockProdutoRequestDTO
        MockEstoque.return_value = mockEstoque
        MockPreco.return_value = mockPreco
        MockPrecoDTO.return_value = mockPrecoDTO
        MockEstoqueDTO.return_value = mockEstoqueDTO
        
        response = self.httpAdapter.criar_produto(mockProdutoRequestDTO)
        
        self.assertEqual(response, {"message": "Produto criado com sucesso"})
        self.catalogoService.criar_produto.assert_called()
        last_call_args, last_call_kwargs = self.catalogoService.criar_produto.call_args
        
        self.assertEqual(last_call_kwargs['sku'], "123")
        self.assertEqual(last_call_kwargs['nome'], "Produto Teste")
        self.assertEqual(last_call_kwargs['descr'], "Descrição Teste")
        self.assertEqual(last_call_kwargs['urlImagem'], "http://imagem")
        self.assertEqual(last_call_kwargs['preco'], mockPreco)
        self.assertEqual(last_call_kwargs['estoque'], mockEstoque)

    @patch('adapter.http_api.EstoqueDTO')
    @patch('adapter.http_api.PrecoDTO')
    @patch('adapter.http_api.Preco')
    @patch('adapter.http_api.Estoque')
    @patch('adapter.http_api.ProdutoRequestDTO')
    def testCriarProdutoComErro400(self, MockProdutoRequestDTO, MockEstoque, MockPreco, MockPrecoDTO, MockEstoqueDTO):
        mockProdutoRequestDTO = Mock()
        mockEstoque = Mock()
        mockPreco = Mock()
        mockEstoqueDTO = Mock()
        mockPrecoDTO = Mock()
        
        mockEstoqueDTO.emEstoque = 10
        mockPrecoDTO.precoLista = 10.0
        mockPrecoDTO.precoDesconto = 9.0
        
        mockProdutoRequestDTO.sku = ""
        mockProdutoRequestDTO.nome = "Produto Teste"
        mockProdutoRequestDTO.descr = "Descrição Teste"
        mockProdutoRequestDTO.urlImagem = "http://imagem"
        mockProdutoRequestDTO.estoque = mockEstoqueDTO
        mockProdutoRequestDTO.preco = mockPrecoDTO

        MockProdutoRequestDTO.return_value = mockProdutoRequestDTO
        MockEstoque.return_value = mockEstoque
        MockPreco.return_value = mockPreco
        MockPrecoDTO.return_value = mockPrecoDTO
        MockEstoqueDTO.return_value = mockEstoqueDTO

        # Configurando o mock para lançar uma exceção SkuInvalido quando criar_produto for chamado
        self.catalogoService.criar_produto.side_effect = SkuInvalido("SKU inválido")
        
        # Verificando se a exceção HTTP 400 é lançada
        with self.assertRaises(HTTPException) as context:
            self.httpAdapter.criar_produto(mockProdutoRequestDTO)
            # Verificando o código de status da exceção
            self.assertEqual(context.exception.status_code, 400)
            self.assertTrue("Erro ao criar produto: SKU inválido" in str(context.exception.detail))