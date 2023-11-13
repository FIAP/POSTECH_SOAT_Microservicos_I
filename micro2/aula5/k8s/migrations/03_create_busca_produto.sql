-- Create the 'busca_produto' database
CREATE DATABASE busca_produto;

-- Create a user for the 'estoque' database
CREATE USER 'busca_produto_user'@'%' IDENTIFIED BY 'Mudar123!';
GRANT ALL PRIVILEGES ON busca_produto.* TO 'busca_produto_user'@'%';

-- Flush privileges to apply changes
FLUSH PRIVILEGES;
