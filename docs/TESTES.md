# Roteiro de testes manuais

Este documento descreve **verificações a executar no computador com Docker**. Não são testes automatizados e não significam que os containers foram executados no ambiente de preparação do repositório.

## Preparação

1. Crie `.env` a partir de `.env.example` e preencha os valores.
2. Execute `docker compose up -d --build`.
3. Execute `docker compose ps` e confirme que o LDAP aparece como `healthy`.
4. Abra http://localhost:8080 e http://localhost:5000/api/health.

## Cenários

| Caso | Procedimento | Resultado esperado |
| --- | --- | --- |
| API saudável | `GET /api/health` após subir os containers | HTTP 200 e LDAP conectado |
| Login autorizado | `POST /api/login` com `ana.souza` e senha demonstrativa | HTTP 200 e JWT |
| Token válido | `GET /api/me` com Bearer token válido | HTTP 200 e dados do usuário |
| Acesso administrativo | `GET /api/admin` com token de `ana.souza` | HTTP 200 |
| Acesso negado por grupo | `GET /api/admin` com token de `carlos.lima` | HTTP 403 |
| Credenciais inválidas | Login com senha incorreta | HTTP 401 |
| Senha vazia | Login com `password` vazio | HTTP 401 |
| Token ausente | `GET /api/me` sem Authorization | HTTP 401 |
| Token inválido | `GET /api/me` com token alterado | HTTP 401 |
| LDAP indisponível | Parar LDAP e consultar `GET /api/health` | HTTP 503, se a API continuar acessível |

As senhas demonstrativas constam em `README.md` e `ldap/bootstrap.ldif`, para uso exclusivo no laboratório.

## Logs

```bash
docker compose logs --tail=100 backend
docker compose logs --tail=100 ldap
```

**Atenção:** `docker compose down -v` remove permanentemente os dados dos volumes deste projeto.
