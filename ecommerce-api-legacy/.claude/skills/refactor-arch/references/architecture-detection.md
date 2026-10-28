# Detecção de Arquitetura

Duas etapas obrigatórias: **evidência estrutural** (diretórios) e **evidência de código** (leitura). Só a segunda separa arquitetura real de pastas decorativas.

## 1. Padrões de diretório → camada candidata

| Diretório / arquivo | Camada candidata | Papel esperado |
|---|---|---|
| `models/`, `entities/`, `model/`, `domain/` | Model | Dados, regras de persistência, invariantes de entidade |
| `schemas/`, `dto/`, `serializers/`, `forms/`, `validators/` | View/DTO | Validação de entrada e formato de saída |
| `views/`, `templates/`, `pages/`, `components/`, `static/` | View | Apresentação |
| `controllers/`, `handlers/`, `api/`, `endpoints/` | Controller/Router | Roteamento + orquestração |
| `routes/`, `routers/` | Controller/Router | Tabela de rotas (pode ser a "View" em APIs) |
| `services/`, `use_cases/`, `core/`, `actions/` | Service | Regra de negócio / casos de uso |
| `repositories/`, `dao/`, `db/` | Data access | SQL e persistência |
| `middlewares/`, `middleware/` | Middleware | Pre/pos-processamento de request |
| `config/`, `settings/`, `configs/` | Config | Configuração centralizada |
| `utils/`, `helpers/`, `common/`, `lib/` | Utilitários | Funções genéricas sem estado |
| `tests/`, `test/`, `spec/`, `__tests__/` | Testes | Testes automatizados |
| `docs/`, `doc/` | Docs | Documentação |
| `scripts/`, `bin/`, `tools/` | Scripts | Automação de build/ops |
| `migrations/`, `alembic/`, `prisma/` | Migrations | Versionamento de schema |
| `src/` | Raiz de código | A estrutura interna é decidida pelo conteúdo |

**Nomes em português/Spanish também contam**: `modelos/`, `controladores/`, `rotas/`, `servicos/`, `utilitarios/`, `configuracao/`.

**Sinais de ausência** (relevantes para a auditoria): nenhum `controllers/`, nenhum `models/`, nenhum `services/`, tudo na raiz.

## 2. Evidência de código — o que ler

1. **Entrypoint** — como o app sobe, o que registra, o que instancia.
2. **2-4 arquivos representativos** — um por diretório de camada candidata, de preferência os maiores.
3. **Amostra de dados** — o arquivo com SQL/queries, se houver.

Perguntas-guia ao ler:

- A rota chama lógica de negócio **direto** ou delega a um service?
- A camada de dados monta **SQL string** ou usa ORM/repositório?
- Há **validação de input** (schema/pydantic/marshmallow/manual) ou o controller insere o body cru?
- Existe **estado global mutável** (lista/dict de módulo, singleton)?
- Configuração vem de **env** ou está **hardcoded**?
- Tratamento de erro está **centralizado** (middleware/error handler) ou espalhado (`try/except` em cada handler)?

## 3. Classificação

Escolha **um** rótulo principal e justifique com caminhos.

### Flat / Monolítico desestruturado
- Sinais: poucos arquivos na raiz, sem pastas de camada, tudo junto — rotas, queries e lógica no mesmo arquivo.
- Referência: `code-smells-project` (`app.py`, `controllers.py`, `models.py`, `database.py` na raiz).

### Monolítico em camadas (Layered)
- Sinais: `routes → services → models`, pastas por camada, dependência apontando para baixo.
- Referência: `task-manager-api` (`routes/`, `services/`, `models/`, `utils/`).

### MVC
- Sinais: separação clara Models / Controllers / Views(Routes) com responsabilidades distintas; Controller orquestra, Model encapsula dados, View devolve representação.
- Distinção de Layered vs MVC: em MVC o Controller coordena Model e View; em Layered o service orquestra e não existe "View" no sentido de apresentação.

### Modular monolith
- Sinais: pastas por **domínio** (`modules/orders/`, `packages/`), não por camada técnica; cada módulo com subpastas próprias.
- Teste: existe uma pasta que é o domínio (`billing/`, `catalog/`) e dentro dela há `models/`, `routes/`?

### Clean / Hexagonal
- Sinais: `domain/`, `application/`, `ports/`, `adapters/`, `infrastructure/`; interfaces de domínio invertendo dependência de frameworks; DI por construtor.

### Base de código única (CLI / script / lib)
- Sinais: sem servidor HTTP, sem rotas; `main.py`/`cli.ts` com `argparse`/`commander`; ou `package.json` sem `express`/`start` de servidor.
- Não reporte como "arquitetura quebrada" — a ausência de camadas é esperada nesse caso.

### Indeterminado
- Evidência insuficiente (projeto vazio, só config, código gerado). Declare o que faltou.

## 4. Métricas a coletar

- **Tamanho:** nº de arquivos de código por linguagem + LOC (exclua vendor, gerados, `*.min.js`).
- **Entrypoint(s):** caminho de cada um.
- **Organização de config:** env vars? `.env`? hardcoded?
- **Testes:** existem? qual framework? (relaciona com "testabilidade" da fase 2)
- **CI/CD, Docker:** presentes?
- **Tamanho dos arquivos maiores** — sinal de God Class (relevante para a auditoria).

## 5. Achados arquiteturais que a análise já revela

Ao fazer a leitura de código, anote candidatos a anti-pattern para a seção "O que a Fase 2 deve auditar" do relatório:

| Observação na leitura | Anti-pattern candidato |
|---|---|
| Controller com SQL string interpolada | SQL Injection |
| Controller com regra de negócio pesada | Lógica de negócio no Controller |
| Loop sobre resultados com query interna | N+1 queries |
| Segredo/porta/chave literal no código | Credencial hardcoded |
| Hash de senha com MD5/SHA1 | Criptografia fraca |
| Estado global mutável | Estado global mutável |
| Arquivo com 3+ domínios misturados | God Class / God Method |
| Sem validação de entrada | Validação ausente |
| Dependência declarada mas não usada | Dependência morta |
| `try/except` genérico engolindo erro | Tratamento de erro genérico |
| SQL embutido sem migration | Schema sem versionamento |

NÃO emita esses como achados de auditoria finais — a Fase 2 confirma, classifica severidade e localiza linha exata. Aqui, apenas sinalize candidatos.
