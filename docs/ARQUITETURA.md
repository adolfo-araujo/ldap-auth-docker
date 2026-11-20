# Arquitetura do projeto

O projeto foi elaborado para demonstrar autenticação centralizada com **OpenLDAP**, autorização baseada em grupos e serviços isolados por redes Docker.

## Serviços

| Serviço | Rede | Porta local | Responsabilidade |
| --- | --- | --- | --- |
| `frontend` | `frontnet` | 8080 | Nginx, HTML/CSS/JS e proxy `/api` |
| `backend` | `frontnet` e `backnet` | 5000 | Flask/Gunicorn, login, emissão e validação JWT |
| `ldap` | `backnet` | 389 | Usuários e grupos do diretório |
| `phpldapadmin` | `backnet` | 8081 | Administração visual do OpenLDAP |

Os ports são publicados **somente em `127.0.0.1`** para evitar exposição direta na rede local, além do próprio computador. A comunicação container-container ocorre pelas redes Docker e nomes dos serviços.

## Caminho de autenticação

1. O usuário informa `username` e `password` ao frontend.
2. O Nginx encaminha `POST /api/login` ao backend.
3. O backend consulta o DN da conta, usando filtro LDAP com escape de caracteres.
4. Um *bind* com o DN encontrado e a senha informada valida as credenciais.
5. A API consulta os grupos (`groupOfNames`) e emite JWT com expiração de 60 minutos.
6. O navegador envia o token no cabeçalho `Authorization: Bearer ...` em chamadas protegidas.
7. A rota `/api/admin` só aceita tokens cujo conjunto de grupos inclui `admins`.

## Estrutura LDAP

```text
dc=uva,dc=local
├── ou=usuarios
│   ├── uid=ana.souza     [fictício]
│   └── uid=carlos.lima   [fictício]
└── ou=grupos
    ├── cn=admins
    └── cn=usuarios
```

O OpenLDAP usa os volumes `ldap_data` e `ldap_config`. A primeira inicialização importa o `ldap/bootstrap.ldif`. Alterações no LDIF **não** redefinem diretórios que já possuem dados persistidos; para recriar o diretório de testes, é preciso remover os volumes (`docker compose down -v`, operação destrutiva).

## Limites do exemplo

- LDAP sem TLS e phpLDAPadmin em HTTP; usar somente localmente.
- Para produção: LDAPS/StartTLS, HTTPS e conta de busca LDAP de leitura restrita, em vez do administrador.
- O JWT contém grupos no momento do login. Alterações no LDAP não revogam automaticamente tokens emitidos.
- O frontend guarda o token em `sessionStorage`, modelo demonstrativo que exige revisão do modelo de ameaças para sistemas reais.
