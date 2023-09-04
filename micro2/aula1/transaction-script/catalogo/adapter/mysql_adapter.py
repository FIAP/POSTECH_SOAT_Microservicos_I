from sqlalchemy import create_engine, Table, MetaData, select, update, insert, Column, String, Text, Integer, Float, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import NoResultFound, IntegrityError
from domain.models import Produto
from adapter.exceptions import DatabaseException
from port.repositories import ProdutoRepository

class ProdutoMySQLAdapter(ProdutoRepository):
    def __init__(self, database_url: str):
        self.__engine = create_engine(database_url)
        self.__metadata = MetaData()

        self.__estoque_table = Table(
            'Estoque', self.__metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('emEstoque', Integer, nullable=False),
            Column('reservado', Integer, nullable=False, default=0)
        )

        # Tabela Preco
        self.__preco_table = Table(
            'Preco', self.__metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('precoLista', Float, nullable=False),
            Column('precoDesconto', Float, nullable=False)
        )

        # Tabela Produto
        self.__produto_table = Table(
            'Produto', self.__metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('sku', String(50), nullable=False, unique=True),
            Column('nome', String(255), nullable=False),
            Column('descr', Text, nullable=False),
            Column('urlImagem', String(255), nullable=False),
            Column('precoId', Integer, ForeignKey('Preco.id')),
            Column('estoqueId', Integer, ForeignKey('Estoque.id'))
        )
        self.__session = sessionmaker(autocommit=False, autoflush=False, bind=self.__engine)

    def inserir(self, produto: Produto, on_duplicate_sku: Exception):
        session = self.__session()
        try:
            # Iniciar transação
            session.begin()

            preco_id = None
            estoque_id = None
            if produto.preco:
                insert_preco = insert(self.__preco_table).values(
                    precoLista=produto.preco.precoLista,
                    precoDesconto=produto.preco.precoDesconto)
                result_preco = session.execute(insert_preco)
                preco_id = result_preco.inserted_primary_key[0]

            if produto.estoque:
                insert_estoque = insert(self.__estoque_table).values(
                    emEstoque=produto.estoque.emEstoque,
                    reservado=produto.estoque.reservado)
                result_estoque = session.execute(insert_estoque)
                estoque_id = result_estoque.inserted_primary_key[0]

            # Inserir Produto
            insert_produto = insert(self.__produto_table).values(
                sku=produto.sku,
                nome=produto.nome,
                descr=produto.descr,
                urlImagem=produto.urlImagem,
                precoId=preco_id,
                estoqueId=estoque_id)
            session.execute(insert_produto)
            # Confirmar as mudanças
            session.commit()
        except IntegrityError:
            # Reverter as mudanças em caso de erro
            session.rollback()
            raise on_duplicate_sku
        except Exception as e:
            # Reverter as mudanças em caso de erro
            session.rollback()
            if type(e) is type(on_duplicate_sku):
                raise

            raise DatabaseException({
                "code": "database.error.insert",
                "message": f"Problema ao inserir produto no banco de dados: {e}",
            })
        
        finally:
            # Fechar a sessão
            session.close()

    def buscarPorSku(self, sku: str, on_not_found: Exception) -> Produto:
        query = select(
            self.__produto_table,
            self.__preco_table,
            self.__estoque_table
        ).select_from(
            self.__produto_table
            .outerjoin(self.__preco_table, self.__produto_table.c.precoId == self.__preco_table.c.id)
            .outerjoin(self.__estoque_table, self.__produto_table.c.estoqueId == self.__estoque_table.c.id)
        ).where(self.__produto_table.c.sku == sku)
        
        with self.__engine.connect() as connection:
            try:
                result = connection.execute(query).fetchone()
                if result is None:
                    raise on_not_found
                
                # Mapear valores para nomes de colunas
                produto_column_names = [column.name for column in self.__produto_table.c]
                preco_column_names = [column.name for column in self.__preco_table.c]
                estoque_column_names = [column.name for column in self.__estoque_table.c]

                produto_dict = dict(zip(produto_column_names, result[0:len(produto_column_names)]))
                preco_dict = dict(zip(preco_column_names, result[len(produto_column_names):len(produto_column_names) + len(preco_column_names)]))
                estoque_dict = dict(zip(estoque_column_names, result[len(produto_column_names) + len(preco_column_names):]))

                # Criar objetos de domínio a partir dos dicionários
                produto = Produto(
                    **produto_dict,
                    preco=preco_dict if preco_dict.get('id') else None,
                    estoque=estoque_dict if estoque_dict.get('id') else None
                )

                return produto
            
            except NoResultFound:
                raise on_not_found
            except Exception as e:
                if type(e) is type(on_not_found):
                    raise

                raise DatabaseException({
                    "code": "database.error.select",
                    "message": f"Problema ao buscar produto no banco de dados: {e}",
                })
            
    def excluir(self, sku: str, on_not_found: Exception):
        session = self.__session()
        try:
            # Iniciar transação
            session.begin()

            # Buscar o produto para obter os IDs relacionados de 'estoque' e 'preco'
            query = select(self.__produto_table.c.estoqueId, self.__produto_table.c.precoId).where(self.__produto_table.c.sku == sku)
            result = session.execute(query).fetchone()

            if result is None:
                raise on_not_found

            estoque_id, preco_id = result

            # Excluir o produto
            delete_query_produto = self.__produto_table.delete().where(self.__produto_table.c.sku == sku)
            session.execute(delete_query_produto)

            # Excluir estoque e preço relacionados, se existirem
            if estoque_id is not None:
                delete_query_estoque = self.__estoque_table.delete().where(self.__estoque_table.c.id == estoque_id)
                session.execute(delete_query_estoque)

            if preco_id is not None:
                delete_query_preco = self.__preco_table.delete().where(self.__preco_table.c.id == preco_id)
                session.execute(delete_query_preco)

            # Confirmar transação
            session.commit()
        except Exception as e:
            session.rollback()
            if type(e) is type(on_not_found):
                raise
            
            raise DatabaseException({
                "code": "database.error.delete",
                "message": f"Problema ao excluir produto no banco de dados: {e}",
            })
        
        finally:
            session.close()

    def atualizar(self, produto: Produto, on_not_found: Exception):
        session = self.__session()
        try:          
            # Iniciar transação
            session.begin()

            # Atualizar informações do produto na tabela 'produto'
            update_query_produto = update(self.__produto_table).where(
                self.__produto_table.c.sku == produto.sku
            ).values(
                nome=produto.nome,
                descr=produto.descr,
                urlImagem=produto.urlImagem
            )
            result_produto = session.execute(update_query_produto)

            # Se o produto não foi encontrado, lançar exceção
            if result_produto.rowcount == 0:
                raise on_not_found

            # Atualizar informações de preço na tabela 'preco', se existirem
            if produto.preco:
                update_query_preco = update(self.__preco_table).where(
                    self.__preco_table.c.id == select(self.__produto_table.c.precoId).where(self.__produto_table.c.sku == produto.sku)
                ).values(
                    precoLista=produto.preco.precoLista,
                    precoDesconto=produto.preco.precoDesconto
                )
                session.execute(update_query_preco)
            
            # Atualizar informações de estoque na tabela 'estoque', se existirem
            if produto.estoque:
                update_query_estoque = update(self.__estoque_table).where(
                    self.__estoque_table.c.id == select(self.__produto_table.c.estoqueId).where(self.__produto_table.c.sku == produto.sku)
                ).values(
                    emEstoque=produto.estoque.emEstoque,
                    reservado=produto.estoque.reservado
                )
                session.execute(update_query_estoque)

            # Confirmar transação
            session.commit()
        except Exception as e:
            session.rollback()
            if type(e) is type(on_not_found):
                raise

            raise DatabaseException({
                "code": "database.error.update",
                "message": f"Problema ao atualizar produto no banco de dados: {e}",
            })
        
        finally:
            session.close()
