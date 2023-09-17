import unittest
from unittest.mock import patch, Mock
from domain.exceptions import *
from domain.services import CatalogoService
import pytest

class TestCatalogoService(unittest.TestCase):

    def setUp(self):
        self.produtoRepository = Mock()
        self.produtoEventPublisher = Mock()
        self.service = CatalogoService(self.produtoRepository, self.produtoEventPublisher)

    @patch('domain.services.Produto')
    @patch('domain.services.Preco')
    @patch('domain.services.Estoque')
    def testCriarProdutoComSucesso(self, MockEstoque, MockPreco, MockProduto):
        mockPreco = Mock()
        mockEstoque = Mock()
        mockProduto = Mock()

        MockPreco.return_value = mockPreco
        MockEstoque.return_value = mockEstoque
        MockProduto.return_value = mockProduto

        self.service.criar_produto("SKU123", "Produto Teste", "Descrição Teste", "http://imagem", mockPreco, mockEstoque)

        MockProduto.assert_called_once_with(sku="SKU123", 
                                            nome="Produto Teste", 
                                            descr="Descrição Teste", 
                                            urlImagem="http://imagem", 
                                            preco=mockPreco, 
                                            estoque=mockEstoque)
        
        self.produtoRepository.inserir.assert_called()
        
        # Extrair argumentos passados para produtoRepository.inserir
        last_call_args, last_call_kwargs = self.produtoRepository.inserir.call_args

        # Validar se o primeiro argumento passado para produtoRepository.inserir é o mockProduto
        self.assertEqual(last_call_args[0], mockProduto)

        # Validar se o segundo argumento passado para produtoRepository.inserir é a exceção ProdutoJaExiste
        self.assertIsInstance(last_call_kwargs.get('on_duplicate_sku'), ProdutoJaExiste)
        
        self.produtoEventPublisher.publicar.assert_called_once_with(mockProduto)

if __name__ == '__main__':
    unittest.main()
