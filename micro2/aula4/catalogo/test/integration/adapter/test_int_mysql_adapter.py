import unittest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from domain.entities import Produto, Estoque, Preco, ItemKit
from domain.exceptions import ProdutoJaExiste, ProdutoNaoEncontrado
from adapter.mysql_adapter import ProdutoMySQLAdapter

class TestIntegrationProdutoMySQLAdapter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Inicialização do adapter para os testes
        cls.engine = create_engine('mysql+mysqlconnector://catalogo_user:Mudar123!@test-db-catalogo:3306/catalogo')
        cls.adapter = ProdutoMySQLAdapter('mysql+mysqlconnector://catalogo_user:Mudar123!@test-db-catalogo:3306/catalogo')

    @classmethod
    def tearDownClass(cls):
        # Drop das tabelas após execução de todos os testes
        cls.adapter._ProdutoMySQLAdapter__metadata.drop_all(cls.engine)

    @classmethod
    def setUp(cls):
        # Criar as tabelas antes de cada teste
        cls.adapter._ProdutoMySQLAdapter__metadata.create_all(cls.engine)

    @classmethod
    def tearDown(cls):
        # Limpar as tabelas após cada teste
        cls.adapter._ProdutoMySQLAdapter__metadata.drop_all(cls.engine)

    def testInserirBuscarProduto(self):
        produto = Produto(
            sku="SKU123", 
            nome="Produto Teste", 
            descr="Descricao Teste", 
            urlImagem="http://imagem", 
            preco=Preco(10.0, 5.0), 
            estoque=Estoque(10, 0)
        )

        try:
            self.adapter.inserir(produto, ProdutoJaExiste("Produto já existente"))
            produto_db = self.adapter.buscarPorSku("SKU123", ProdutoNaoEncontrado("Produto não encontrado"))
            self.assertEqual(produto_db.sku, produto.sku)
            self.assertEqual(produto_db.nome, produto.nome)
            self.assertEqual(produto_db.descr, produto.descr)
            self.assertEqual(produto_db.urlImagem, produto.urlImagem)
            self.assertEqual(produto_db.preco.precoLista, produto.preco.precoLista)
            self.assertEqual(produto_db.preco.precoDesconto, produto.preco.precoDesconto)
            self.assertEqual(produto_db.estoque.emEstoque, produto.estoque.emEstoque)
            self.assertEqual(produto_db.estoque.reservado, produto.estoque.reservado)
        except Exception as e:
            self.fail(f"Gerada exceção: {e}")

    def testInserirDuplicado(self):
        produto = Produto(
            sku="SKU123", 
            nome="Produto Teste", 
            descr="Descricao Teste", 
            urlImagem="http://imagem", 
            preco=Preco(10.0, 5.0), 
            estoque=Estoque(10, 0)
        )

        self.adapter.inserir(produto, on_duplicate_sku=ProdutoJaExiste("Produto já existente"))

        with self.assertRaises(ProdutoJaExiste):
            self.adapter.inserir(produto, on_duplicate_sku=ProdutoJaExiste("Produto já existente"))

    def testBuscarProdutoInexistente(self):
        with self.assertRaises(ProdutoNaoEncontrado):
            self.adapter.buscarPorSku("SKU_INEXISTENTE", ProdutoNaoEncontrado("Produto não encontrado"))

if __name__ == '__main__':
    unittest.main()
