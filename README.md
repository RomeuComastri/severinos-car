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
- [Banco de dados](#banco-de-dados)
- [Criando usuários](#criando-usuários)
- [Imagens dos veículos](#imagens-dos-veículos)
- [Executando com Docker](#executando-com-docker)
- [Autenticação](#autenticação)
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
| 2 | Cadastro de veículos com imagem | `app/modules/veiculos` | `feature/crud-veiculos` |
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
| Armazenamento de imagens | Supabase Storage |
| Testes | Pytest |
| Container | Docker e Docker Compose |
| Hospedagem | Render |

## Estrutura do projeto

```
severinos-car/
├── app/
│   ├── core/
│   │   ├── config.py          Leitura das variáveis de ambiente
│   │   ├── database.py        Conexão com o banco e sessão por requisição
│   │   ├── security.py        Hash de senha (bcrypt) e geração/validação de JWT
│   │   └── storage.py         Envio e remoção de arquivos no Supabase Storage
│   ├── modules/
│   │   ├── health/            Verificação da API e do banco
│   │   ├── auth/              Card 1: login, proteção das rotas e criação de usuários
│   │   ├── veiculos/          Card 2: CRUD de veículos e imagem
│   │   ├── compradores/       Card 3
│   │   └── vendas/            Card 4
│   └── main.py                Criação da aplicação e registro das rotas
├── db/
│   └── migrations/            Scripts SQL executados manualmente no Supabase
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
Os módulos de negócio são registrados com `dependencies=[Depends(get_current_user)]`, o que faz
todas as suas rotas exigirem login (veja [Autenticação](#autenticação)).

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
| `JWT_SECRET_KEY` | Sim | Chave que assina os tokens de login. Sem ela, o login responde `503` |
| `APP_NAME` | Não | Título exibido na documentação. Padrão: `Severinos Car API` |
| `JWT_EXPIRE_MINUTES` | Não | Validade do token, em minutos. Padrão: `30` |
| `SUPABASE_URL` | Para imagens | URL do projeto no Supabase (`https://<id>.supabase.co`) |
| `SUPABASE_SECRET_KEY` | Para imagens | Secret key do projeto. Sem ela, o envio de imagens responde `503` |
| `SUPABASE_STORAGE_BUCKET` | Não | Bucket das imagens dos veículos. Padrão: `veiculos` |

Para gerar a `JWT_SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Use uma chave diferente em cada ambiente. Trocar a chave invalida todos os tokens emitidos,
o que obriga todos os usuários a fazer login novamente.

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

**5. Prepare o banco** (apenas na primeira vez): execute as migrações e crie um usuário, conforme
[Banco de dados](#banco-de-dados) e [Criando usuários](#criando-usuários).

**6. Inicie a API**

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

## Banco de dados

As tabelas são criadas por scripts SQL versionados em `db/migrations/`, executados manualmente no
Supabase em **SQL Editor > New query**. Cada migração tem um script de rollback correspondente.

| Ordem | Script | O que faz | Rollback |
|-------|--------|-----------|----------|
| 001 | `001_cria_tabela_usuarios.sql` | Cria a tabela `usuarios` com e-mail único e RLS habilitado | `001_cria_tabela_usuarios_rollback.sql` |
| 002 | `002_cria_tabela_veiculos.sql` | Cria a tabela `veiculos` com placa única, preço maior que zero e RLS habilitado | `002_cria_tabela_veiculos_rollback.sql` |

Os scripts usam `IF NOT EXISTS` e podem ser executados mais de uma vez. Execute-os em cada
projeto do Supabase usado pelos ambientes.

O RLS (Row Level Security) bloqueia o acesso à tabela pela API REST pública do Supabase, que usa
a chave `anon`. A nossa API conecta com o usuário `postgres` e não é afetada.

Ao criar ou alterar um model em `app/modules/*/models.py`, crie um novo script numerado
(`003_...sql`) com o rollback correspondente.

## Criando usuários

Não há rota de cadastro na API. Os usuários são criados por um comando de terminal, que grava no
banco configurado na `DATABASE_URL` do `.env`:

```bash
python -m app.modules.auth.cli criar-usuario --nome "João Silva" --email joao@loja.com
```

A senha é pedida duas vezes, sem aparecer na tela. Regras:

- O e-mail precisa ser válido e não pode estar cadastrado. É salvo em letras minúsculas.
- A senha precisa ter no mínimo 8 caracteres e no máximo 72 bytes (limite do bcrypt).
- A senha é armazenada apenas como hash bcrypt, nunca em texto puro.

Para desativar um usuário sem apagá-lo, execute no SQL Editor
`UPDATE usuarios SET ativo = false WHERE email = 'joao@loja.com';`. Ele perde o acesso
imediatamente, inclusive com tokens já emitidos.

## Imagens dos veículos

As imagens são armazenadas no Supabase Storage. O banco guarda apenas a URL pública da imagem,
no campo `imagem_url` do veículo.

**Configuração (uma vez por projeto do Supabase):**

1. Em **Storage**, crie um bucket chamado `veiculos` e marque-o como **Public bucket**.
2. Em **Project Settings > API Keys**, copie uma **Secret key** (`sb_secret_...`).
3. Preencha `SUPABASE_URL` e `SUPABASE_SECRET_KEY` no `.env` e nos serviços do Render.

A secret key dá acesso total ao projeto do Supabase. Ela deve existir apenas no `.env` e nas
variáveis do Render, nunca no código.

**Regras de envio:**

- Formatos aceitos: JPEG, PNG e WEBP, identificados pelo conteúdo do arquivo e não pela extensão.
- Tamanho máximo: 5 MB.
- Cada veículo tem uma imagem. Ao enviar uma nova, a anterior é removida do Storage.
- Ao excluir o veículo ou a imagem, o arquivo também é removido do Storage.

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

## Autenticação

A API usa login com e-mail e senha e token JWT (`Bearer`), válido por 30 minutos.

1. Faça login em `POST /auth/login` e copie o `access_token` da resposta.
2. Envie o token nas demais requisições, no header `Authorization: Bearer <token>`.
3. Quando o token expirar, faça login novamente. Não há refresh token.

No Swagger (`/docs`), clique em **Authorize**, cole o token e confirme. As requisições feitas
pela página passam a enviar o header automaticamente.

**Rotas públicas:** `/`, `/health`, `/health/db`, `/docs`, `/redoc` e `POST /auth/login`. Todas
as demais exigem token. Qualquer falha de autenticação (token ausente, inválido, expirado ou de
usuário desativado) retorna:

```json
// 401
{ "detail": "Não autenticado." }
```

Para proteger um novo módulo, registre o router em `app/main.py` com a dependência de
autenticação. Para obter o usuário logado dentro de uma rota, declare-o como parâmetro:

```python
app.include_router(veiculos_router, dependencies=[Depends(get_current_user)])

@router.get("/minha-rota")
def minha_rota(usuario: Usuario = Depends(get_current_user)): ...
```

## Endpoints

A documentação completa, com possibilidade de testar as requisições, está disponível no Swagger
(`/docs`).

| Método | Rota | Descrição | Autenticação | Respostas |
|--------|------|-----------|--------------|-----------|
| `GET` | `/health` | Verifica se a API está no ar | Pública | `200` |
| `GET` | `/health/db` | Verifica a conexão com o banco de dados | Pública | `200`, `503` |
| `POST` | `/auth/login` | Autentica o usuário e devolve um token JWT | Pública | `200`, `401`, `422`, `503` |
| `GET` | `/auth/me` | Retorna os dados do usuário logado | Token | `200`, `401` |
| `POST` | `/veiculos` | Cadastra um veículo | Token | `201`, `400`, `401`, `422` |
| `GET` | `/veiculos` | Lista os veículos, com filtro opcional `?status=disponivel` ou `vendido` | Token | `200`, `401` |
| `GET` | `/veiculos/{id}` | Busca um veículo pelo ID | Token | `200`, `401`, `404` |
| `PUT` | `/veiculos/{id}` | Atualiza todos os dados de um veículo, inclusive o status | Token | `200`, `400`, `401`, `404`, `422` |
| `DELETE` | `/veiculos/{id}` | Exclui um veículo que não foi vendido | Token | `204`, `400`, `401`, `404` |
| `PUT` | `/veiculos/{id}/imagem` | Envia ou substitui a imagem (`multipart/form-data`, campo `arquivo`) | Token | `200`, `400`, `401`, `404`, `503` |
| `DELETE` | `/veiculos/{id}/imagem` | Remove a imagem do veículo | Token | `204`, `401`, `404` |

### Regras de negócio dos veículos

| Regra | Resposta em caso de violação |
|-------|------------------------------|
| Placa obrigatória, no formato `ABC1234` ou Mercosul `ABC1D23` (salva em maiúsculas, sem traço) | `422` |
| Placa única entre todos os veículos | `400` |
| Ano entre 1900 e o ano atual + 1 | `422` |
| Preço maior que zero | `422` |
| Veículo novo é sempre cadastrado como `disponivel`, mesmo que outro status seja enviado | - |
| Veículo com status `vendido` não pode ser excluído | `400` |

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

`POST /auth/login`

```json
// requisição
{ "email": "joao@loja.com", "senha": "minhaSenha123" }

// 200
{ "access_token": "eyJhbGciOiJIUzI1NiIs...", "token_type": "bearer", "expires_in": 1800 }

// 401: e-mail inexistente, senha incorreta ou usuário desativado
{ "detail": "E-mail ou senha inválidos." }
```

`GET /auth/me` com `Authorization: Bearer <token>` (200)

```json
{ "id": 1, "nome": "João Silva", "email": "joao@loja.com" }
```

`POST /veiculos`

```json
// requisição
{ "placa": "ABC1D23", "marca": "Volkswagen", "modelo": "Gol", "ano": 2022, "cor": "Prata", "preco": 55000.00 }

// 201
{
  "id": 1, "placa": "ABC1D23", "marca": "Volkswagen", "modelo": "Gol", "ano": 2022, "cor": "Prata",
  "preco": 55000.0, "status": "disponivel", "imagem_url": null, "criado_em": "2026-11-17T14:00:00Z"
}

// 400: placa já cadastrada
{ "detail": "Já existe um veículo com a placa ABC1D23." }

// 422: dados inválidos (um item por campo inválido)
{ "detail": [{ "loc": ["body", "preco"], "msg": "Value error, O preço deve ser maior que zero.", "...": "..." }] }
```

`PUT /veiculos/{id}` exige todos os campos do cadastro e também o `status` (`disponivel` ou `vendido`).

`DELETE /veiculos/{id}` (400, veículo vendido)

```json
{ "detail": "Não é possível excluir um veículo vendido." }
```

`GET /veiculos/{id}` (404)

```json
{ "detail": "Veículo não encontrado." }
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
| `usuario_cadastrado` | Usuário ativo `joao@loja.com`, com a senha `SENHA_DE_TESTE` |
| `auth_headers` | Header `Authorization` com um token válido do `usuario_cadastrado` |
| `storage_fake` | Storage em memória que registra envios e remoções, usado no lugar do Supabase Storage |
| `veiculo_cadastrado` | Veículo disponível de placa `ABC1D23` (em `tests/veiculos/conftest.py`) |

O `conftest.py` define uma `JWT_SECRET_KEY` própria para os testes antes de importar a API, e o
`client` usa o `storage_fake`. Por isso os testes não dependem do `.env`, da chave real nem do
Supabase Storage.

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
| auth | `test_login_valido_retorna_token` | `POST /auth/login` com e-mail e senha corretos | Status 200 e `access_token` preenchido |
| auth | `test_senha_incorreta_retorna_401` | `POST /auth/login` com senha incorreta | Status 401 e `E-mail ou senha inválidos.` |
| core | `test_chave_secreta_nova_vai_somente_no_header_apikey` | Secret key `sb_secret_...` | Chave apenas no header `apikey` |
| core | `test_chave_legada_service_role_vai_tambem_no_header_authorization` | Chave legada (JWT) | Chave nos headers `apikey` e `Authorization` |
| core | `test_converte_caminho_em_url_publica_e_vice_versa` | Caminho `1/foto.jpg` e URLs | URL pública correta e caminho extraído; `None` para URL externa |
| core | `test_envio_sem_configuracao_lanca_erro` | Storage sem URL e chave | Exceção `StorageNotConfiguredError` |
| veiculos | `test_cadastra_veiculo_valido` | `POST /veiculos` com placa `abc-1234` | Status 201 e placa salva como `ABC1234` |
| veiculos | `test_veiculo_novo_nasce_disponivel_mesmo_com_status_informado` | `POST /veiculos` com `status: vendido` | Status 201 e `status: disponivel` |
| veiculos | `test_rejeita_placa_duplicada` | `POST /veiculos` com placa já cadastrada | Status 400 e mensagem de placa duplicada |
| veiculos | `test_rejeita_cadastro_sem_placa` | `POST /veiculos` sem o campo `placa` | Status 422 |
| veiculos | `test_rejeita_placa_em_formato_invalido` (5 casos) | Placas vazia, curta, longa e fora do padrão | Status 422 e `Placa inválida` |
| veiculos | `test_rejeita_ano_invalido` (2 casos) | Ano 1899 e ano atual + 2 | Status 422 e faixa de anos válida |
| veiculos | `test_rejeita_preco_menor_ou_igual_a_zero` (2 casos) | Preço 0 e negativo | Status 422 e `O preço deve ser maior que zero.` |
| veiculos | `test_lista_veiculos` | `GET /veiculos` com dois veículos | Status 200 e os dois veículos em ordem |
| veiculos | `test_filtra_veiculos_por_status` | `GET /veiculos?status=vendido` | Somente o veículo vendido |
| veiculos | `test_busca_veiculo_por_id` | `GET /veiculos/{id}` | Status 200 e os dados do veículo |
| veiculos | `test_veiculo_inexistente_retorna_404` (3 casos) | `GET`, `PUT` e `DELETE` em `/veiculos/999` | Status 404 e `Veículo não encontrado.` |
| veiculos | `test_atualiza_veiculo` | `PUT /veiculos/{id}` com cor, preço e status novos | Status 200 e dados atualizados |
| veiculos | `test_atualizacao_rejeita_placa_de_outro_veiculo` | `PUT` com a placa de outro veículo | Status 400 e mensagem de placa duplicada |
| veiculos | `test_exclui_veiculo_disponivel` | `DELETE /veiculos/{id}` | Status 204 e veículo não encontrado depois |
| veiculos | `test_nao_exclui_veiculo_vendido` | `DELETE` em veículo vendido | Status 400 e veículo mantido |
| veiculos | `test_rotas_de_veiculos_exigem_autenticacao` (7 casos) | Todas as rotas de veículos sem token | Status 401 e `Não autenticado.` |
| veiculos | `test_envia_imagem_e_salva_a_url_no_veiculo` (3 casos) | Imagens JPEG, PNG e WEBP | Status 200 e `imagem_url` com a extensão do formato |
| veiculos | `test_rejeita_arquivo_que_nao_e_imagem` | Arquivo PDF com extensão `.jpg` | Status 400 e nada enviado ao Storage |
| veiculos | `test_rejeita_imagem_maior_que_5_mb` | Imagem acima de 5 MB | Status 400 e nada enviado ao Storage |
| veiculos | `test_envio_de_imagem_para_veiculo_inexistente_retorna_404` | Imagem para `/veiculos/999` | Status 404 |
| veiculos | `test_substituir_imagem_remove_a_anterior_do_storage` | Duas imagens seguidas | A primeira é removida do Storage |
| veiculos | `test_remove_imagem_do_veiculo` | `DELETE /veiculos/{id}/imagem` | Status 204, `imagem_url` nula e arquivo removido |
| veiculos | `test_excluir_veiculo_remove_a_imagem_do_storage` | `DELETE /veiculos/{id}` com imagem | Status 204 e arquivo removido |
| veiculos | `test_envio_de_imagem_sem_storage_configurado_retorna_503` | Imagem sem `SUPABASE_URL` e chave | Status 503 e `Serviço de imagens indisponível.` |

## Ambientes e deploy

A mesma imagem Docker é publicada em dois serviços no Render. O deploy é feito pelo GitHub
Actions, somente após a aprovação dos testes.

| Ambiente | Branch | Serviço no Render | Publicado quando |
|----------|--------|-------------------|------------------|
| Homologação | `develop` | `hml-severinos-car` | Merge na `develop` |
| Produção | `main` | `severinos-car` | Merge de `release/*` ou `hotfix/*` na `main` |

| Ambiente | URL |
|----------|-----|
| Homologação | https://hml-severinos-car.onrender.com/docs |
| Produção | https://severinos-car.onrender.com/docs |

Variáveis configuradas em cada serviço: `DATABASE_URL`, `JWT_SECRET_KEY` (diferente em cada
ambiente), `SUPABASE_URL`, `SUPABASE_SECRET_KEY` e `APP_NAME`. O Health Check Path dos
serviços é `/health`.

No plano gratuito do Render, o serviço hiberna após um período sem requisições. A primeira
chamada após a hibernação pode levar até um minuto.

### Pipelines (GitHub Actions)

| Workflow | Gatilho | Etapas |
|----------|---------|--------|
| `ci.yml` | Pull Request para `develop` ou `main` | Executa os testes |
| `deploy-hml.yml` | Push (merge) na `develop` | Testes, deploy em homologação |
| `release-prod.yml` | Merge de `release/X.Y.Z` ou `hotfix/X.Y.Z` na `main` | Testes, deploy em produção, criação da release `vX.Y.Z` no GitHub |

Se os testes falharem, o deploy não é executado e a versão anterior permanece no ar. A versão da
release é obtida do nome da branch: `release/1.2.0` gera a tag `v1.2.0`, com notas geradas a
partir dos Pull Requests incluídos.

### Configuração inicial

1. No Render, criar os dois Web Services (runtime Docker), cada um apontando para sua branch,
   com as variáveis de ambiente, o Health Check Path `/health` e o **Auto-Deploy desativado**.
2. Copiar o **Deploy Hook** de cada serviço (Settings do serviço no Render).
3. No GitHub, em **Settings > Secrets and variables > Actions**, cadastrar os secrets
   `RENDER_DEPLOY_HOOK_HML` e `RENDER_DEPLOY_HOOK_PROD`.
4. Recomendado: em **Settings > Branches**, proteger `develop` e `main` exigindo Pull Request e
   a aprovação do check **Testes automatizados**.

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
4. Após o merge, a funcionalidade é publicada automaticamente em homologação.
5. Para publicar em produção, crie `release/X.Y.Z` a partir de `develop` e abra um Pull Request
   para `main`. Após o merge, a API é publicada em produção e a release `vX.Y.Z` é criada.
   Se houver ajustes na branch de release, integre-os de volta em `develop`.
6. Correções urgentes partem de `main` em `hotfix/X.Y.Z` e são integradas em `main` e `develop`.

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
2. Registre o router em `app/main.py` com `dependencies=[Depends(get_current_user)]`, para que
   suas rotas exijam login. Se o módulo tiver tabelas, crie o script em `db/migrations/`.
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
| Login retorna `503 Autenticação indisponível` | `JWT_SECRET_KEY` não configurada | Defina a variável no `.env` ou no Render e reinicie |
| Login retorna `401` com a senha correta | Usuário desativado ou e-mail diferente do cadastrado | Confira a tabela `usuarios` no Supabase |
| Todas as rotas protegidas retornam `401` | Token expirado (30 min), header sem `Bearer ` ou chave trocada | Faça login novamente |
| `relation "usuarios" does not exist` | Migração não executada no banco | Execute `db/migrations/001_cria_tabela_usuarios.sql` |
| `relation "veiculos" does not exist` | Migração não executada no banco | Execute `db/migrations/002_cria_tabela_veiculos.sql` |
| Envio de imagem retorna `503` | `SUPABASE_URL` ou `SUPABASE_SECRET_KEY` ausentes, chave inválida ou bucket inexistente | Confira as variáveis e o bucket `veiculos`; o motivo aparece no log da API |
| Imagem enviada, mas a URL não abre | Bucket não está público | Em **Storage**, marque o bucket `veiculos` como **Public bucket** |
