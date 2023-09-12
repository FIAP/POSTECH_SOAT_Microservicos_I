-- Create a user for the 'catalogo' database
CREATE USER 'catalogo_user'@'%' IDENTIFIED BY 'Mudar123!';
GRANT ALL PRIVILEGES ON catalogo.* TO 'catalogo_user'@'%';

-- Flush privileges to apply changes
FLUSH PRIVILEGES;
