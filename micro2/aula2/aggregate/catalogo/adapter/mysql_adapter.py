from sqlalchemy import create_engine, Table, MetaData, select, update, insert, Column, String, Text, Integer, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import NoResultFound, IntegrityError
from typing import Optional, List
from domain.entities import Produto, ItemKit
from domain.value_objects import Estoque, Preco
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
            Column('versao', Integer, nullable=False, default=0),
            Column('sku', String(50), nullable=False, unique=True),
            Column('nome', String(255), nullable=False),
            Column('descr', Text, nullable=False),
            Column('urlImagem', String(255), nullable=False),
            Column('precoId', Integer, ForeignKey('Preco.id')),
            Column('estoqueId', Integer, ForeignKey('Estoque.id'))
        )

        # Tabela ItemKit
        self.__item_kit_table = Table(
            'ItemKit', self.__metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('versao', Integer, nullable=False, default=0),
            Column('kitId', Integer, ForeignKey('Produto.id')),
            Column('produtoId', Integer, ForeignKey('Produto.id')),
            Column('qtd', Integer, nullable=False),
            Column('precoId', Integer, ForeignKey('Preco.id')),
            UniqueConstraint('kitId', 'produtoId', name='uix_1')
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

            if produto.kit is not None and len(produto.kit) > 0:
                for itemKit in produto.kit:
                    insert_preco_item_kit = insert(self.__preco_table).values(
                        precoLista=itemKit.preco.precoLista,
                        precoDesconto=itemKit.preco.precoDesconto)
                    result_preco_item_kit = session.execute(insert_preco_item_kit)
                    preco_id_item_kit = result_preco_item_kit.inserted_primary_key[0]
                    insert_item_kit = insert(self.__item_kit_table).values(
                        versao=0,
                        kitId=produto.id,
                        produtoId=itemKit.produtoId,
                        qtd=itemKit.qtd,
                        precoId=preco_id_item_kit)
                    session.execute(insert_item_kit)

            # Inserir Produto
            insert_produto = insert(self.__produto_table).values(
                versao=0,
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
                estoque = Estoque(**estoque_dict) if estoque_dict.get('id') else None
                preco = Preco(**preco_dict) if preco_dict.get('id') else None
                kit = self.busca_lista_item_kit(produto_dict.get('id'))
                produto = Produto(
                    **produto_dict,
                    preco=preco,
                    estoque=estoque,
                    kit=kit
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
            query = select(self.__produto_table.c.id ,self.__produto_table.c.estoqueId, self.__produto_table.c.precoId).where(self.__produto_table.c.sku == sku)
            result = session.execute(query).fetchone()

            if result is None:
                raise on_not_found

            produto_id, estoque_id, preco_id = result


            # Deletar itens de kit relacionados, se existirem
            query_lista_item_kit = select(self.__item_kit_table.c.precoId).where(self.__item_kit_table.c.kitId == produto_id)
            result_lista_item_kit = session.execute(query_lista_item_kit).fetchall()

            delete_query_item_kit = self.__item_kit_table.delete().where(self.__item_kit_table.c.kitId == produto_id)
            session.execute(delete_query_item_kit)

            for result_item_kit in result_lista_item_kit:
                delete_query_preco_item_kit = self.__preco_table.delete().where(self.__preco_table.c.id == result_item_kit[0])
                session.execute(delete_query_preco_item_kit)
            
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

    def atualizar(self, produto: Produto, on_not_found: Exception, on_outdated_version: Exception, on_duplicate: Exception):
        session = self.__session()
        try:          
            # Iniciar transação
            session.begin()

            query = select(self.__produto_table.c.versao).where(self.__produto_table.c.sku == produto.sku)
            result = session.execute(query).fetchone()

            # Se o produto não foi encontrado, lançar exceção
            if result is None:
                raise on_not_found
            versao = result[0]
            nova_versao = versao + 1

            # Atualizar informações do produto na tabela 'produto'
            update_query_produto = update(self.__produto_table).where(
                self.__produto_table.c.sku == produto.sku,
                self.__produto_table.c.versao == versao
            ).values(
                nome=produto.nome,
                descr=produto.descr,
                urlImagem=produto.urlImagem,
                versao=nova_versao
            )
            result_produto = session.execute(update_query_produto)

            # Se versão desatualizada, lançar exceção
            if result_produto.rowcount == 0:
                raise on_outdated_version

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

            if produto.kit is not None and len(produto.kit) > 0:
                query_lista_item_kit = select(self.__item_kit_table.c.id, self.__item_kit_table.c.versao, self.__item_kit_table.c.precoId).where(self.__item_kit_table.c.kitId == produto.id)
                result_lista_item_kit = session.execute(query_lista_item_kit).fetchall()
                lista_atualizar = []
                lista_inserir = []
                lista_deletar = []
                for itemKit in produto.kit:
                    atualizar = False
                    for result_item_kit in result_lista_item_kit:
                        if result_item_kit[0] == itemKit.id:
                            lista_atualizar.append(itemKit)
                            atualizar = True
                            break
                    if not atualizar:
                        lista_inserir.append(itemKit)
                for result_item_kit in result_lista_item_kit:
                    deletar = True
                    for itemKit in produto.kit:
                        if result_item_kit[0] == itemKit.id:
                            deletar = False
                            break
                    if deletar:
                        lista_deletar.append(result_item_kit[0])

                for itemKit in lista_atualizar:
                    result_item_kit = None
                    for result in result_lista_item_kit:
                        if result[0] == itemKit.id:
                            result_item_kit = result
                            break
                    versao_item_kit = result_item_kit[1]
                    nova_versao_item_kit = versao_item_kit + 1
                    update_query_item_kit = update(self.__item_kit_table).where(
                        self.__item_kit_table.c.id == result_item_kit[0]
                    ).values(
                        versao=nova_versao_item_kit,
                        qtd=itemKit.qtd
                    )
                    session.execute(update_query_item_kit)

                    update_query_preco_item_kit = update(self.__preco_table).where(
                        self.__preco_table.c.id == result_item_kit[2]
                    ).values(
                        precoLista=itemKit.preco.precoLista,
                        precoDesconto=itemKit.preco.precoDesconto
                    )
                    session.execute(update_query_preco_item_kit)
                for itemKit in lista_inserir:
                    insert_preco_item_kit = insert(self.__preco_table).values(
                        precoLista=itemKit.preco.precoLista,
                        precoDesconto=itemKit.preco.precoDesconto)
                    result_preco_item_kit = session.execute(insert_preco_item_kit)
                    preco_id_item_kit = result_preco_item_kit.inserted_primary_key[0]
                    insert_item_kit = insert(self.__item_kit_table).values(
                        versao=0,
                        kitId=produto.id,
                        produtoId=itemKit.produtoId,
                        qtd=itemKit.qtd,
                        precoId=preco_id_item_kit)
                    session.execute(insert_item_kit)
                for itemKit in lista_deletar:
                    delete_query_item_kit = self.__item_kit_table.delete().where(self.__item_kit_table.c.id == itemKit)
                    session.execute(delete_query_item_kit)

            elif produto.kit is not None and len(produto.kit) == 0:
                delete_query_item_kit = self.__item_kit_table.delete().where(self.__item_kit_table.c.kitId == produto.id)
                session.execute(delete_query_item_kit)
                
            # Confirmar transação
            session.commit()
            
        except IntegrityError as e:
            session.rollback()
            if e.orig.args[0] == 1062:
                raise on_duplicate
            elif e.orig.args[0] == 1452:
                raise on_not_found
            print(f"SQL Error code: {e.orig.args[0]}")
            raise
        except Exception as e:
            session.rollback()
            if type(e) is type(on_not_found) or type(e) is type(on_outdated_version) or type(e) is type(on_duplicate):
                raise

            raise DatabaseException({
                "code": "database.error.update",
                "message": f"Problema ao atualizar produto no banco de dados: {e}",
            })
        
        finally:
            session.close()
    
    def busca_lista_item_kit(self, kit_id: int) -> Optional[List[ItemKit]]:
        query = select(
            self.__item_kit_table,
            self.__preco_table
        ).select_from(
            self.__item_kit_table
            .outerjoin(self.__preco_table, self.__item_kit_table.c.precoId == self.__preco_table.c.id)
        ).where(self.__item_kit_table.c.kitId == kit_id)
        with self.__engine.connect() as connection:
            try:
                result = connection.execute(query).fetchall()
                
                # Mapear valores para nomes de colunas
                item_kit_column_names = [column.name for column in self.__item_kit_table.c]
                preco_column_names = [column.name for column in self.__preco_table.c]

                item_kit_list = []
                for row in result:
                    item_kit_dict = dict(zip(item_kit_column_names, row[0:len(item_kit_column_names)]))
                    preco_dict = dict(zip(preco_column_names, row[len(item_kit_column_names):]))

                    # Criar objetos de domínio a partir dos dicionários
                    preco = Preco(**preco_dict) if preco_dict.get('id') else None
                    item_kit = ItemKit(
                        **item_kit_dict,
                        preco=preco
                    )

                    item_kit_list.append(item_kit)

                return item_kit_list
            
            except Exception as e:
                raise DatabaseException({
                    "code": "database.item_kit.error.select",
                    "message": f"Problema ao buscar lista de item de kit no banco de dados: {e}",
                })