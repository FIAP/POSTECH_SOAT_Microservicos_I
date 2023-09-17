import unittest
from domain.entities import Produto
from domain.value_objects import ItemKitDetalhe, Preco, Estoque
from domain.exceptions import *
import pytest

class TestProduto(unittest.TestCase):
    def testValidarSkuInvalido(self):
        with self.assertRaises(SkuInvalido):
            Produto(nome="Nome", descr="Descr", urlImagem="http://imagem", sku="")

    def testValidarNomeInvalido(self):
        with self.assertRaises(ProdutoInvalido):
            Produto(nome="", descr="Descr", urlImagem="http://imagem", sku="123")

    def testValidarDescrInvalido(self):
        with self.assertRaises(ProdutoInvalido):
            Produto(nome="Nome", descr="", urlImagem="http://imagem", sku="123")

    def testValidarUrlImagemInvalido(self):
        with self.assertRaises(ProdutoInvalido):
            Produto(nome="Nome", descr="Descr", urlImagem="invalido", sku="123")

    def testValidarPrecoValido(self):
        produto = Produto(nome="Nome", descr="Descr", urlImagem="http://imagem", sku="123", preco=Preco(10.0, 5.0))
        self.assertEqual(produto.preco.precoLista, 10.0)
        self.assertEqual(produto.preco.precoDesconto, 5.0)

    def testValidarPrecoInvalido(self):
        with self.assertRaises(PrecoInvalido):
            Produto(nome="Nome", descr="Descr", urlImagem="http://imagem", sku="123", preco=Preco(10.0, 15.0))
    
    def testValidarEstoqueValido(self):
        produto = Produto(nome="Nome", descr="Descr", urlImagem="http://imagem", sku="123", estoque=Estoque(10))
        self.assertEqual(produto.estoque.emEstoque, 10)

    def testValidarEstoqueInvalido(self):
        with self.assertRaises(EstoqueInvalido):
            Produto(nome="Nome", descr="Descr", urlImagem="http://imagem", sku="123", estoque=Estoque(-1))

class TestProdutoItemKit(unittest.TestCase):
    def setUp(self):
        self.produto = Produto(id=1,
                               nome="Produto Teste", 
                               sku="123456789",
                               descr="Produto para lampada...", 
                               urlImagem="https://imagem.fiapstore.com.br/sku/123456789.png")  
        
    def testInserirListaItemKitListaVazia(self):
        with self.assertRaises(ListaItemKitInvalida):
            self.produto.inserirListaItemKit([])

    def testInserirListaItemKitProdutoJaNoKit(self):
        with self.assertRaises(ItemKitInvalido):
            item1 = ItemKitDetalhe(2, 10, Preco(20.0, 10.0))
            self.produto.inserirListaItemKit([item1])
            self.produto.inserirListaItemKit([item1])

    def test_obterItemKitItemNaoEncontrado(self):
        with self.assertRaises(ItemKitNaoEncontrado):
            self.produto.obterItemKit(2)

    def testValidarPrecoListaItemKitPrecoListaInferiorAoMinimo(self):
        item1 = ItemKitDetalhe(2, 10, Preco(5.0, 4.0)) 
        item2 = ItemKitDetalhe(3, 20, Preco(5.0, 4.0))
        with self.assertRaises(ListaItemKitInvalida):
            self.produto.inserirListaItemKit([item1, item2])

    def testValidarPrecoListaItemKitPrecoDescontoInferiorAoMinimo(self):
        item1 = ItemKitDetalhe(2, 10, Preco(16.0, 4.99)) 
        item2 = ItemKitDetalhe(3, 20, Preco(16.0, 5.0))
        with self.assertRaises(ListaItemKitInvalida):
            self.produto.inserirListaItemKit([item1, item2])

    def testValidarPrecoListaItemKitPrecosValidos(self):
        item1 = ItemKitDetalhe(2, 10, Preco(8.0, 5.0)) 
        item2 = ItemKitDetalhe(3, 20, Preco(7.0, 5.0))
        try:
            self.produto.inserirListaItemKit([item1, item2])
        except ListaItemKitInvalida:
            self.fail("ListaItemKitInvalida foi lançada, mas não deveria")

if __name__ == "__main__":
    unittest.main()