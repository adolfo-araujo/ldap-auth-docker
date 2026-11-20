# Publicar no GitHub

## Identificação sugerida

- **Nome do repositório:** `ldap-auth-docker`
- **Descrição:** `API de autenticação LDAP com Flask e JWT, controle de acesso por grupos e infraestrutura Docker com OpenLDAP e Nginx.`
- **Visibilidade:** público (apenas para dados fictícios e serviços não expostos à internet)
- **README:** não criar na tela inicial do GitHub; ele já existe aqui
- **.gitignore:** não criar na tela inicial do GitHub; ele já existe aqui
- **Licença:** não adicionar sem decidir a licença apropriada

## Antes do primeiro commit

1. Confirme que o arquivo `.env` **não** foi incluído. Se tiver sido publicado anteriormente, altere a senha LDAP e o segredo JWT, além de removê-lo do histórico.
2. Revise `ldap/bootstrap.ldif`: ele contém **contas de teste públicas**, com senhas conhecidas. Não utilize identidades ou dados reais.
3. Verifique se nenhum log, token, certificado privado, arquivo de chave ou banco de produção será enviado.
4. Os screenshots são capturas do relatório acadêmico, não incluem o relatório completo nem a matrícula do aluno.
5. Faça os testes descritos em `TESTES.md` antes de apresentar o projeto como executável.

## Primeira publicação usando Git

```bash
git init
git add .
git status
git commit -m "docs: prepara projeto LDAP para portfolio"
git branch -M main
git remote add origin https://github.com/adolfo-araujo/ldap-auth-docker.git
git push -u origin main
```

O repositório remoto deve ser criado antes; para um repositório existente, adapte `git remote add origin` para `git remote set-url origin` ou utilize `git clone` para preservar o histórico.

## Publicação pela interface do GitHub

1. Crie um repositório vazio, sem README, .gitignore ou licença automáticos.
2. Extraia o ZIP de distribuição deste projeto.
3. Use **Add file → Upload files** e envie o conteúdo da pasta extraída, incluindo arquivos ocultos `.gitignore` e `.env.example`.
4. Faça o commit e confira a árvore de arquivos. **Não envie o ZIP inteiro como substituto dos arquivos.**

## Aviso de execução

Os comandos de inicialização dependem de Docker e Docker Compose instalados. Esta versão foi revisada por análise estática; faça o teste integrado no seu computador.
