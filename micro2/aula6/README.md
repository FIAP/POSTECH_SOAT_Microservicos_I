# Elastic
## Disclaimer
> Recomenda-se uma VM Linux com 2 CPU (64-bit), 4 GiB RAM e 30 GiB Disco.

> Na VM Linux, configurar o `vm.max_map_count` com o valor `262144`. Para isso, usar o seguinte comando: `sudo sysctl -w vm.max_map_count=262144`. Para persistir essa configuração em caso de reboot da VM, editar o arquivo `/etc/sysctl.conf` utilizando o comando `sudo nano /etc/sysctl.conf`, inserindo a seguinte linha no final do arquivo: `vm.max_map_count = 262144`.

## Configuração de índices
### Politica de ILM
```json
PUT _ilm/policy/fiap-store-logs // Nome da política
{
    "policy": {
        "_meta": { // Metadados da política
            "description": "Logs da aplicação FIAP Store",
            "project": {
                "name": "FIAP Store",
                "department": "TI"
            }
        },
        "phases": { // Fases da política
            "hot": { 
                "min_age": "0ms", // Tempo mínimo para a fase
                "actions": { // Ações da fase
                    "rollover": {
                        // "max_age": "15d" // Tempo máximo para a fase
                        "max_docs": 10 // Número máximo de documentos
                        // "max_primary_shard_size": "32gb" // Tamanho máximo do shard primário
                    }
                }
            },
            "warm": {
                "min_age": "0ms",
                "actions": {
                        "readonly": {}, // Indica que o index é somente leitura
                        "forcemerge": { // Força o merge de shards
                            "max_num_segments": 1 // Número máximo de shards
                        },
                        "shrink": { // Reduz o número de shards
                                "max_primary_shard_size": "50gb" // Tamanho máximo do shard primário
                        }
                }
            },
            "delete": {
                "min_age": "30d",
                "actions": {
                    "delete": { // Deleta o index
                        "delete_searchable_snapshot": true // Deleta o snapshot
                    }
                }
            }
        }
    }
}
```

### Template
```json
PUT _template/fiap-store-logs // Nome do template
{
    "settings": { // Configurações do index
        "number_of_shards": 2, // Número de shards
        "number_of_replicas": 0, // Número de réplicas
        "index.lifecycle.name": "fiap-store-logs", // Nome da política de ILM     
        "index.lifecycle.rollover_alias": "fiap-store-logs" // Alias para o index
    },
    "index_patterns": ["fiap-store-logs-*"], // Padrão de nome para o index
    "mappings": { // Mapeamento dos campos do index
        "properties": { 
            "data_hora": { "type": "date" }, // Data e hora do evento
            "tipo": { "type": "keyword" }, // produto, pedido, cliente, etc
            "sku": { "type": "keyword" }, // Código do produto
            "nome": { "type": "keyword" }, // Nome do produto
            "descricao": { "type": "text" }, // Descrição do produto
            "categoria": { "type": "keyword" }, // Categoria do produto
            "quantidade": { "type": "integer" }, // Quantidade do produto disponível em estoque
            "preco": { // Preço do produto
                "properties": {
                    "desconto": { "type": "float" }, // Desconto
                    "lista": { "type": "float" } // Preço de lista
                }
            }
        }
    }
}
```

### Criação de index
```json
PUT /fiap-store-logs-000001/ // Nome do index
{
    "aliases": { // Alias para o index
        "fiap-store-logs": {
            "is_write_index": true // Indica que é o index atual
        }
    }
}
```


### Envio de docs exemplo
```json
POST /fiap-store-logs/_doc/
{
  "data_hora": "2023-10-20T09:00:30.264-03:00",
  "tipo": "produto",
  "sku": "123456",
  "nome": "Lâmpada LED 7W",
  "descricao": "Lâmpada LED 7W Branca Fria",
  "categoria": "Iluminação",
  "quantidade": 20,
  "preco": {
    "desconto": 5.00,
    "lista": 10.00
  }
}

POST /fiap-store-logs/_doc/
{
  "data_hora": "2023-10-15T14:20:30.160Z",
  "tipo": "produto",
  "sku": "123457",
  "nome": "Lâmpada LED 9W",
  "descricao": "Lâmpada LED 9W Branca Quente",
  "categoria": "Iluminação",
  "quantidade": 30,
  "preco": {
    "desconto": 10.50,
    "lista": 14.70
  }
}

POST /fiap-store-logs/_doc/
{
  "data_hora": "2023-10-10T10:20:30.190-03:00",
  "tipo": "produto",
  "sku": "321450",
  "nome": "Régua de Tomadas 5T",
  "descricao": "Régua de tomadas com 5 tomadas 2P+T 10A/250V",
  "categoria": "Elétrica",
  "quantidade": 10,
  "preco": {
    "desconto": 18.00,
    "lista": 22.00
  }
}
```

## Referências
- https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html
- https://www.elastic.co/guide/en/elasticsearch/reference/current/index-templates.html
- https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping-types.html
- https://www.elastic.co/guide/en/elasticsearch/reference/current/index-lifecycle-management.html