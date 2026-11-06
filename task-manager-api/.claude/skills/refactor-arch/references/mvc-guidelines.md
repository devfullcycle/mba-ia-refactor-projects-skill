# MVC Guidelines — Fase 3 (Refatoração)

Diretrizes **agnósticas de linguagem** para reestruturar um projeto Flat/desestruturado em arquitetura em camadas (MVC + Services + Repositories). A tradução para o ecossistema concreto vem de dois lugares: o **relatório da Fase 1** (linguagem, framework e convenções detectadas) e a **tabela de mapeamento da seção 3** deste documento.

## 1. Camadas e responsabilidades (conceitual)

| Camada | Responsabilidade | NÃO contém |
|---|---|---|
| **Router/Routes** | Mapear URL + verbo → handler do controller. Só registro. | Lógica, queries, validação |
| **Controller/Handler** | Orquestrar: extrair input do request → validar schema básico → chamar service → serializar resposta com status correto. Máximo ~50 linhas por handler. | SQL, regras de negócio, cálculos, loops sobre entidades |
| **Service/Use-case** | Regras de negócio: cálculos, validações complexas, orquestração entre repositories. Lança erros de domínio. Não conhece o protocolo de transporte. | HTTP (request/response), SQL |
| **Repository/DAO** | Único ponto de acesso a dados. Toda query é parametrizada. Recebe e devolve estruturas de dados simples ou entidades. | HTTP, regras de negócio |
| **Model/Entity** | Invariantes de domínio, validação de entidade, factory methods. | SQL, HTTP |
| **Config** | Configuração centralizada lida de variáveis de ambiente, com defaults seguros. | Segredos literais |
| **Middleware** | Pré/pós-processamento de request: auth, logging, CORS, tratamento de erro. | Regras de negócio |

**Teste de pertencimento:** se um trecho de código não pode ser testado sem subir o servidor HTTP, ele não pertence ao Controller. Se não pode ser testado sem banco, não pertence ao Service.

## 2. Estrutura alvo (conceitual)

```
projeto/
├── <entrypoint>            # só cria a aplicação, registra rotas, inicializa recursos
├── <config>                # configuração via ambiente
├── routes/                 # registro de rotas, agrupadas por recurso
├── controllers/            # orquestração request → service → response
├── services/               # regras de negócio, agrupadas por domínio
├── repositories/           # acesso a dados, um por entidade agregada
├── models/                 # entidades e invariantes de domínio
├── middleware/             # guards e cross-cutting concerns
├── utils/                  # funções genéricas sem estado
├── tests/                  # testes automatizados
└── reports/                # relatórios emitidos por esta skill
```

Notas:
- Os nomes acima são **conceituais**. Use a nomenclatura dominante do ecossistema (seção 3), não esta tabela literalmente.
- **Frameworks com convenção própria** (Rails, Django, Laravel, Spring) já impõem uma estrutura — siga a convenção do framework em vez de forçar esta árvore.
- Um arquivo por recurso/domínio dentro de cada camada (ex.: um controller por recurso, um repository por entidade agregada).

## 3. Mapeamento por ecossistema

Tradução dos conceitos para as stacks mais comuns. Se a stack do projeto não estiver aqui, aplique os conceitos da seção 1 com as convenções do framework detectado e registre a lacuna no relatório.

| Conceito | Python/Flask | Python/Django | Node/Express | Java/Spring |
|---|---|---|---|---|
| Router | `Blueprint` | `urls.py` | `Router()` | `@RequestMapping` |
| Controller | módulo de handlers | `views.py` | handlers | `@RestController` |
| Service | `services/` | `services/` (custom) | `services/` | `@Service` |
| Repository | `repositories/` | ORM (`Manager`) | `repositories/` | `@Repository` |
| Model/Entity | classes de domínio | `models.py` | `models/` | `@Entity` |
| Config | módulo + `os.environ` | `settings.py` + env | `process.env` + dotenv | `application.yml` |
| Middleware | `@app.before_request` | `middleware.py` | `app.use()` | `Filter` / `HandlerInterceptor` |
| Error handler | `@app.errorhandler` | handler de exceção | middleware `(err, req, res, next)` | `@ControllerAdvice` |

| Conceito | Ruby/Rails | PHP/Laravel | Go (Gin/Echo) | C#/ASP.NET |
|---|---|---|---|---|
| Router | `config/routes.rb` | `routes/api.php` | `router.Group()` | `[Route]` / `MapControllers` |
| Controller | `app/controllers/` | `app/Http/Controllers/` | handlers | `ControllerBase` |
| Service | `app/services/` (custom) | `app/Services/` (custom) | `services/` | services via DI |
| Repository | ActiveRecord | Eloquent / Repository | `repositories/` | `DbContext` / Repository |
| Model/Entity | `app/models/` | `app/Models/` | structs | classes de domínio |
| Config | `ENV` + credentials | `.env` + `config/` | `os.Getenv` / viper | `appsettings.json` |
| Middleware | middleware Rack | `app/Http/Middleware/` | `Use()` | middleware pipeline |
| Error handler | `rescue_from` | `Handler.php` | middleware de recovery | `UseExceptionHandler` |

## 4. Regras de refatoração

- **R1 — Preserve funcionalidade.** Cada endpoint existente mantém a mesma URL, verbo e formato de resposta, a menos que o relatório de auditoria exija mudança explícita.
- **R2 — Uma mudança por vez.** Não misture reestruturação com correção de bugs no mesmo passo. Estruture primeiro, corrija depois (ou em commits separados).
- **R3 — Mova, não copie.** Ao extrair código para uma nova camada, remova-o do arquivo original. Sem duplicatas.
- **R4 — Commits pequenos.** Cada unidade movida (ex.: repository de uma entidade) = um commit.
- **R5 — Teste após cada passo.** Após mover uma entidade completa (route → controller → service → repository), suba a aplicação e exercite os endpoints afetados antes de prosseguir.
- **R6 — Compatibilidade de resposta.** Se o formato de resposta mudar, documente no relatório da Fase 3. O ideal é manter compatibilidade total.
- **R7 — Configuração externalizada.** Portas, hosts, paths, flags e segredos saem do código para variáveis de ambiente com defaults seguros (resolve QUAL-07 e SEC-02).
- **R8 — Queries parametrizadas.** Toda query usa o placeholder da stack (`?`, `%s`, `$1`, `:nome`, `@nome` — ver tabela no `refactor-playbook.md`). Nunca interpolação de string em SQL (resolve SEC-01).
- **R9 — Segredos fora do código.** Credenciais, chaves e tokens vêm de ambiente ou gerenciador de segredos, nunca literais (resolve SEC-02).
- **R10 — Erro centralizado.** Use o mecanismo de error handler do framework (seção 3) em vez de blocos de captura genérica repetidos em cada handler (resolve QUAL-03).
- **R11 — Segurança por padrão.** Auth e autorização existem no default do projeto; nenhuma correção pode depender de flag opcional (`AUTH_REQUIRED=true`). Se o contrato mudar, atualize os testes em vez de manter o achado aberto.
- **R12 — Autorização por papel e posse.** Gestão de usuários exige `admin`; rotas de domínio exigem o papel adequado. Identidade, papel e dono do recurso são derivados do token — nunca de `role`, `tipo`, `usuario_id` ou `owner_id` enviados pelo cliente.

## 5. Ordem de execução

1. **Config** — criar o ponto central de configuração; mover literais para ambiente.
2. **Persistência** — separar conexão de inicialização de schema/seed; eliminar estado global mutável desprotegido.
3. **Repositories** — um por entidade agregada; reescrever queries com parâmetros.
4. **Services** — extrair regras de negócio dos controllers para services por domínio.
5. **Controllers** — reduzir handlers a orquestração pura (request → service → response).
6. **Routes** — separar o registro de rotas do entrypoint, agrupando por recurso.
7. **Middleware/Auth** — aplicar autenticação e autorização **default deny** (Padrão 9 do playbook) em rotas de escrita e administrativas; sem flag opt-in (SEC-04).
8. **Cleanup** — remover arquivos antigos, dead code e imports mortos.
9. **Validação** — executar o checklist da seção 6.

## 6. Validação pós-refatoração

O checklist é **derivado do inventário de rotas da Fase 1** — não existe lista fixa de endpoints. Para cada rota inventariada, registre o resultado no relatório da Fase 3.

- [ ] A aplicação sobe sem erros, usando o comando de boot identificado na Fase 1
- [ ] Toda rota inventariada na Fase 1 responde no mesmo path, verbo e formato de contrato
- [ ] Rotas de escrita rejeitam payload malformado/ausente com status 400
- [ ] Nenhuma query interpolada restante — grep por concatenação/interpolação em chamadas SQL
- [ ] Nenhum segredo literal no código — grep pelos padrões de SEC-02
- [ ] Responses não expõem campos sensíveis (senhas, tokens, chaves internas)
- [ ] Rotas de escrita rejeitam anônimo por padrão (`401`)
- [ ] Rotas administrativas rejeitam não-admin (`403`)
- [ ] Identidade, papel e posse vêm do token, nunca do body
- [ ] Nenhuma senha em texto puro em seed/banco (hash com salt em todo armazenamento)
- [ ] Nenhum CRITICAL/HIGH em `PARCIAL` ou `NÃO RESOLVIDO`
- [ ] Nenhum bloco de captura genérica que engole erro sem log (QUAL-03)
- [ ] Arquivos antigos removidos; nenhum import/dependência morta restante
- [ ] `git status` limpo de sobras da refatoração (arquivos órfãos, diretórios vazios)
