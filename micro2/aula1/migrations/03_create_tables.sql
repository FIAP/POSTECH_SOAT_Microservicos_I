-- Usar o banco de dados 'catalogo'
USE catalogo;

-- Criação da tabela Estoque
CREATE TABLE Estoque (
    id INT PRIMARY KEY AUTO_INCREMENT,
    emEstoque INT NOT NULL,
    reservado INT DEFAULT 0
);

-- Criação da tabela Preco
CREATE TABLE Preco (
    id INT PRIMARY KEY AUTO_INCREMENT,
    precoLista FLOAT NOT NULL,
    precoDesconto FLOAT NOT NULL
);

-- Criação da tabela Produto
CREATE TABLE Produto (
    id INT PRIMARY KEY AUTO_INCREMENT,
    versao INT NOT NULL,
    sku VARCHAR(50) NOT NULL UNIQUE,
    nome VARCHAR(255) NOT NULL,
    descr TEXT NOT NULL,
    urlImagem VARCHAR(255) NOT NULL,
    precoId INT,
    estoqueId INT,
    FOREIGN KEY (precoId) REFERENCES Preco(id),
    FOREIGN KEY (estoqueId) REFERENCES Estoque(id)
);

-- Criação da tabela ItemKit
CREATE TABLE ItemKit (
    id INT PRIMARY KEY AUTO_INCREMENT,
    versao INT NOT NULL,
    kitId INT,
    produtoId INT NOT NULL,
    qtd INT,
    precoId INT,
    FOREIGN KEY (kitId) REFERENCES Produto(id),
    FOREIGN KEY (produtoId) REFERENCES Produto(id),
    FOREIGN KEY (precoId) REFERENCES Preco(id),
    UNIQUE (kitId, produtoId)
);