-- Create a user for the 'estoque' database
CREATE USER 'estoque_user'@'%' IDENTIFIED BY 'Mudar123!';
GRANT ALL PRIVILEGES ON estoque.* TO 'estoque_user'@'%';

-- Create a user for the 'precificacao' database
CREATE USER 'precificacao_user'@'%' IDENTIFIED BY 'Mudar123!';
GRANT ALL PRIVILEGES ON precificacao.* TO 'precificacao_user'@'%';

-- Create a user for the 'catalogo' database
CREATE USER 'catalogo_user'@'%' IDENTIFIED BY 'Mudar123!';
GRANT ALL PRIVILEGES ON catalogo.* TO 'catalogo_user'@'%';

-- Flush privileges to apply changes
FLUSH PRIVILEGES;
