# Severinos Car API

API REST para gestão de lojas de veículos: autenticação de funcionários, cadastro de veículos,
cadastro de compradores e registro de vendas.

Projeto desenvolvido para o Trabalho Prático da disciplina **Gestão da Qualidade de Software**
(Ciência da Computação, UNIFENAS, 2026/2), com foco em testes automatizados e versionamento
com Gitflow.

## Sumário

- [Funcionalidades](#funcionalidades)
- [Tecnologias](#tecnologias)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Pré-requisitos](#pré-requisitos)
- [Configuração](#configuração)
- [Executando localmente](#executando-localmente)
- [Executando com Docker](#executando-com-docker)
- [Endpoints](#endpoints)
- [Testes automatizados](#testes-automatizados)
- [Ambientes e deploy](#ambientes-e-deploy)
- [Fluxo de trabalho](#fluxo-de-trabalho)
- [Solução de problemas](#solução-de-problemas)

## Funcionalidades

Cada funcionalidade corresponde a um card do Kanban e a um módulo independente do código.

| Card | Funcionalidade | Módulo | Branch |
|------|----------------|--------|--------|
| 0 | Setup do projeto | `app/core` | `feature/setup-projeto` |
| 1 | Login de usuário com token JWT | `app/modules/auth` | `feature/login-jwt` |
| 2 | Cadastro de veículos | `app/modules/veiculos` | `feature/crud-veiculos` |
| 3 | Cadastro de compradores | `app/modules/compradores` | `feature/crud-compradores` |
| 4 | Registro de venda de veículo | `app/modules/vendas` | `feature/crud-vendas` |

## Tecnologias

| Camada | Tecnologia |
|--------|------------|
| Linguagem | Python 3.10 ou superior (imagem Docker usa 3.13) |
| Framework web | FastAPI |
| Servidor ASGI | Uvicorn |
| ORM | SQLAlchemy 2 |
| Banco de dados | PostgreSQL hospedado no Supabase |
| Testes | Pytest |
| Container | Docker e Docker Compose |
| Hospedagem | Render |

## Estrutura do projeto

```
severinos-car/
├── app/
│   ├── core/
│   │   ├── config.py          Leitura das variáveis de ambiente
│   │   └── database.py        Conexão com o banco e sessão por requisição
│   ├── modules/
│   │   ├── health/            Verificação da API e do banco
│   │   ├── auth/              Card 1
│   │   ├── veiculos/          Card 2
│   │   ├── compradores/       Card 3
│   │   └── vendas/            Card 4
│   └── main.py                Criação da aplicação e registro das rotas
├── tests/
│   ├── conftest.py            Fixtures compartilhadas
│   ├── core/
│   ├── health/
│   └── ...                    Uma pasta por módulo
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── pytest.ini
└── requirements.txt
```

### Organização de um módulo

Todos os módulos seguem a mesma divisão em camadas. Cada integrante trabalha apenas na pasta do
seu módulo, o que reduz conflitos de merge.

| Arquivo | Responsabilidade |
|---------|------------------|
| `router.py` | Rotas HTTP. Recebe a requisição e delega para o service. |
| `schemas.py` | Modelos de entrada e saída (Pydantic). |
| `models.py` | Tabelas do banco (SQLAlchemy, herdando de `Base`). |
| `service.py` | Regras de negócio. Camada principal dos testes unitários. |
| `repository.py` | Consultas e gravações no banco. |

Para ativar um módulo, descomente o import e o `include_router` correspondentes em `app/main.py`.

## Pré-requisitos

- [Python 3.10+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (apenas para executar com Docker)
- Acesso ao projeto do Supabase (solicite a connection string a um integrante da equipe)

## Configuração

A aplicação lê suas configurações de variáveis de ambiente ou de um arquivo `.env` na raiz do
projeto. Crie o arquivo a partir do modelo:

```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `DATABASE_URL` | Sim | Connection string do PostgreSQL no Supabase |
| `APP_NAME` | Não | Título exibido na documentação. Padrão: `Severinos Car API` |

### Obtendo a `DATABASE_URL`

1. No painel do Supabase, abra o projeto e clique em **Connect**.
2. Em **Connection String**, selecione o formato **URI** e copie a string do **Session pooler**.
3. Cole o valor no `.env` e substitua `[YOUR-PASSWORD]` pela senha do banco, sem os colchetes.

Use a string completa copiada do painel: o host e a região variam de projeto para projeto.
A conexão direta (`db.<projeto>.supabase.co`) não deve ser usada, pois exige IPv6, que não está
disponível no Render.

O arquivo `.env` contém credenciais e está no `.gitignore`. Ele nunca deve ser commitado.

## Executando localmente

**1. Clone o repositório**

```bash
git clone <url-do-repositorio>
cd severinos-car
```

**2. Crie e ative o ambiente virtual**

```bash
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate
```

**3. Instale as dependências**

```bash
pip install -r requirements.txt
```

**4. Configure o `.env`** conforme a seção [Configuração](#configuração).

**5. Inicie a API**

```bash
uvicorn app.main:app --reload
```

| Recurso | Endereço |
|---------|----------|
| API | http://localhost:8000 |
| Swagger (documentação interativa) | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

Para confirmar que a conexão com o banco está funcionando, acesse
http://localhost:8000/health/db. A resposta esperada é `{"status": "ok", "database": "connected"}`.

O `--reload` reinicia a API quando arquivos `.py` são alterados, mas não quando o `.env` muda.
Após editar o `.env`, pare a API com `Ctrl+C` e inicie novamente.

## Executando com Docker

Com o Docker Desktop em execução e o `.env` configurado:

```bash
docker compose up --build
```

A API ficará disponível nos mesmos endereços da execução local (porta 8000). Para encerrar:

```bash
docker compose down
```

A imagem contém apenas o código da aplicação e suas dependências. O `.env` não é copiado para a
imagem: localmente ele é carregado pelo Docker Compose e, no Render, as variáveis são definidas
no painel do serviço. A porta é lida da variável `PORT`, definida automaticamente pelo Render.

## Endpoints

A documentação completa, com possibilidade de testar as requisições, está disponível no Swagger
(`/docs`).

| Método | Rota | Descrição | Respostas |
|--------|------|-----------|-----------|
| `GET` | `/health` | Verifica se a API está no ar | `200` |
| `GET` | `/health/db` | Verifica a conexão com o banco de dados | `200`, `503` |

**Exemplos de resposta**

`GET /health` (200)

```json
{ "status": "ok" }
```

`GET /health/db` (200)

```json
{ "status": "ok", "database": "connected" }
```

`GET /health/db` (503, banco indisponível)

```json
{ "status": "error", "database": "unavailable" }
```

## Testes automatizados

### Estratégia

- Framework: **Pytest**, com o `TestClient` do FastAPI para testar as rotas.
- Os testes **não acessam o Supabase**. A dependência de banco (`get_db`) é substituída por um
  SQLite em memória ou por objetos falsos que simulam falhas. Assim os testes são rápidos,
  independentes entre si e executam sem internet e sem `.env`.
- Cada teste segue o padrão preparar, executar e verificar, com nomes que descrevem o
  comportamento esperado.
- A organização de `tests/` espelha a de `app/modules/`.

### Fixtures disponíveis (`tests/conftest.py`)

| Fixture | Descrição |
|---------|-----------|
| `db_session` | Sessão SQLite em memória, recriada a cada teste |
| `client` | Cliente HTTP da API já usando o `db_session` no lugar do banco real |

### Executando

```bash
# Todos os testes
pytest

# Testes de um módulo
pytest tests/health

# Um teste específico
pytest tests/health/test_health.py::test_health_retorna_status_ok
```

### Casos de teste

| Módulo | Teste | Entrada | Resultado esperado |
|--------|-------|---------|--------------------|
| core | `test_url_do_supabase_e_convertida_para_driver_psycopg` | URL `postgresql://` | URL com prefixo `postgresql+psycopg://` |
| core | `test_url_do_supabase_e_convertida_para_driver_psycopg` | URL `postgres://` | URL com prefixo `postgresql+psycopg://` |
| core | `test_url_do_supabase_e_convertida_para_driver_psycopg` | URL `postgresql+psycopg://` | URL mantida sem alteração |
| core | `test_url_do_banco_e_none_quando_nao_configurada` | `DATABASE_URL` ausente | `None` |
| core | `test_get_engine_lanca_erro_quando_database_url_nao_configurada` | `DATABASE_URL` ausente | Exceção `DatabaseNotConfiguredError` |
| health | `test_health_retorna_status_ok` | `GET /health` | Status 200 e `status: ok` |
| health | `test_health_db_retorna_conectado_quando_banco_responde` | `GET /health/db` com banco disponível | Status 200 e `database: connected` |
| health | `test_health_db_retorna_503_quando_banco_indisponivel` | `GET /health/db` com banco indisponível | Status 503 e `database: unavailable` |

## Ambientes e deploy

A mesma imagem Docker é publicada em dois serviços no Render. O deploy é automático a cada
merge na branch correspondente.

| Ambiente | Branch | Serviço no Render |
|----------|--------|-------------------|
| Homologação | `develop` | `severinos-car-hml` |
| Produção | `main` | `severinos-car-prod` |

Variáveis configuradas em cada serviço: `DATABASE_URL` e `APP_NAME`. O Health Check Path dos
serviços é `/health`.

No plano gratuito do Render, o serviço hiberna após um período sem requisições. A primeira
chamada após a hibernação pode levar até um minuto.

## Fluxo de trabalho

### Gitflow

| Branch | Finalidade |
|--------|------------|
| `main` | Versão estável, publicada em produção |
| `develop` | Integração das funcionalidades, publicada em homologação |
| `feature/*` | Desenvolvimento de um card |
| `release/*` | Preparação de uma versão para produção |
| `hotfix/*` | Correção urgente em produção |

1. Crie a branch do card a partir de `develop`: `git checkout -b feature/nome-do-card develop`.
2. Desenvolva a funcionalidade com seus testes e garanta que `pytest` passa localmente.
3. Abra um Pull Request para `develop`.
4. Para publicar em produção, crie `release/x.y.z` a partir de `develop`, abra um Pull Request
   para `main` e, após o merge, integre a release de volta em `develop`.
5. Correções urgentes partem de `main` em `hotfix/*` e são integradas em `main` e `develop`.

### Mensagens de commit

O projeto segue o padrão [Conventional Commits](https://www.conventionalcommits.org/pt-br/):

| Prefixo | Uso | Exemplo |
|---------|-----|---------|
| `feat` | Nova funcionalidade | `feat: adiciona cadastro de veículos` |
| `fix` | Correção de erro | `fix: corrige validação de placa duplicada` |
| `test` | Criação ou ajuste de testes | `test: cobre venda de veículo já vendido` |
| `docs` | Documentação | `docs: descreve endpoints de compradores` |
| `refactor` | Melhoria de código sem mudar comportamento | `refactor: extrai validação para o service` |
| `chore` | Configuração e manutenção | `chore: atualiza dependências` |

### Adicionando um novo módulo

1. Crie os arquivos do módulo em `app/modules/<modulo>/` seguindo a
   [organização de um módulo](#organização-de-um-módulo).
2. Registre o router em `app/main.py`.
3. Escreva os testes em `tests/<modulo>/`, usando as fixtures `client` e `db_session`.
4. Atualize as tabelas de [Endpoints](#endpoints) e [Casos de teste](#casos-de-teste) deste README.

## Solução de problemas

| Sintoma | Causa provável | Solução |
|---------|----------------|---------|
| `/health/db` retorna 503 | Falha de conexão com o banco | Verifique o erro exibido no terminal da API |
| `tenant/user ... not found` | Host do pooler incorreto | Copie a string completa em **Connect > Session pooler** |
| `password authentication failed` | Senha incorreta | Confira a senha no `.env` ou redefina no Supabase |
| Conexão falha com senha correta | Senha com `@`, `#`, `/`, `:` ou `%` | Use uma senha apenas com letras e números |
| Alteração no `.env` não surte efeito | API não foi reiniciada | Pare com `Ctrl+C` e inicie novamente |
| Erro ao ativar o `.venv` no PowerShell | Execução de scripts bloqueada | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Porta 8000 em uso | API local e Docker rodando juntos | Encerre uma das execuções |
