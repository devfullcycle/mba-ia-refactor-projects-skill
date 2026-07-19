# Fase 2 — Catálogo de Anti-Patterns e Critérios de Severidade

Este catálogo é a base da auditoria. Cada entrada tem: **sinais de detecção** concretos (o que
procurar no código), a **severidade** e por quê. Use-o como checklist, mas não se limite a ele —
você é um engenheiro sênior; qualquer problema real de arquitetura, segurança, concorrência,
qualidade, SOLID ou MVC deve virar finding, mesmo que não esteja listado aqui.

## Critérios de classificação de severidade

Classifique **todo** finding segundo esta tabela:

- **CRITICAL** — Falhas graves de arquitetura ou segurança que impedem o funcionamento correto,
  expõem dados sensíveis (ex.: credenciais hardcoded, SQL Injection) ou violam completamente a
  separação de responsabilidades (ex.: "God Class" com banco, lógica e roteamento no mesmo arquivo).
- **HIGH** — Fortes violações do padrão MVC ou de SOLID que dificultam muito manutenção e testes
  (ex.: lógica de negócio pesada presa em Controllers/rotas, forte acoplamento sem Injeção de
  Dependência, estado global mutável na aplicação inteira).
- **MEDIUM** — Problemas de padronização, duplicação de código ou performance moderada
  (ex.: N+1 no banco, uso inadequado de middlewares, validações ausentes nas rotas).
- **LOW** — Legibilidade, nomenclatura ruim de variáveis, "magic numbers" soltos.

Na dúvida entre dois níveis, pese o **impacto**: pode vazar dado ou derrubar a app? → sobe para CRITICAL.
É só cosmético? → LOW.

## Como escrever um finding

Cada finding precisa de **arquivo e linhas exatas**. Formato (ver `03-report-templates.md`):

```
[SEVERIDADE] <Título curto do problema>
File: <arquivo>:<linha ou intervalo>
Description: <o que é o problema, concreto>
Impact: <consequência prática>
Recommendation: <como corrigir — aponte a transformação do playbook quando houver>
```

---

## Catálogo

### AP-01 — God Class / God Module — **CRITICAL**
**O que é:** um único arquivo/classe concentra responsabilidades de várias camadas (dados, regra
de negócio, roteamento, formatação) e/ou de vários domínios.
**Sinais:** arquivo muito longo (centenas de linhas) misturando SQL, validação, regra e resposta
HTTP; uma classe `Manager`/`Helper`/`models.py` que faz tudo; múltiplos domínios no mesmo arquivo.
**Impacto:** impossível testar em isolamento; qualquer mudança arrisca quebrar tudo; viola SRP.
**Recomendação:** separar em models e controllers por domínio.

### AP-02 — Hardcoded Credentials / Secrets — **CRITICAL**
**O que é:** segredos fixos no código (SECRET_KEY, chaves de API, senhas, tokens).
**Sinais:** `SECRET_KEY = "..."`, `paymentGatewayKey`, `password = "123"`, chaves em strings literais.
**Impacto:** exposição de credenciais em qualquer clone/commit; comprometimento de segurança.
**Recomendação:** mover para variáveis de ambiente / módulo de config (`os.environ`, `.env`).

### AP-03 — SQL Injection / Query dinâmica insegura — **CRITICAL**
**O que é:** SQL montado por concatenação/interpolação de input do usuário, ou endpoint que executa
SQL arbitrário.
**Sinais:** `f"SELECT ... {var}"`, `"... " + req.body.x`, `cursor.execute(query_do_usuario)`,
rota tipo `/admin/query` que roda SQL recebido.
**Impacto:** leitura/escrita arbitrária no banco; vazamento e destruição de dados.
**Recomendação:** usar sempre queries parametrizadas; remover endpoints de SQL arbitrário.

### AP-04 — Senha em texto puro / criptografia fraca — **CRITICAL**
**O que é:** senhas armazenadas/comparadas em texto puro ou com hash caseiro/inseguro.
**Sinais:** `INSERT INTO users (... pass) VALUES (..., '123')`, comparação direta `senha == input`,
função `badCrypto`, uso de `md5`/`sha1` sem salt para senha.
**Impacto:** vazamento direto de credenciais dos usuários em caso de breach.
**Recomendação:** hashing forte com salt (`bcrypt`, `argon2`, `werkzeug.security`).

### AP-05 — Estado global mutável / Singleton implícito — **HIGH**
**O que é:** conexão de banco ou configuração guardada em variável global mutável compartilhada.
**Sinais:** `db_connection = None` global reatribuída; `global db_connection`; instância única de
conexão passeando pela app; `check_same_thread=False` para contornar o problema.
**Impacto:** acoplamento forte, condições de corrida, dificíssimo de testar e paralelizar.
**Recomendação:** injeção de dependência; factory de conexão; escopo por request.

### AP-06 — Lógica de negócio na camada de rota/controller — **HIGH**
**O que é:** regra de negócio, acesso a dados e orquestração misturados dentro do handler da rota.
**Sinais:** handler que abre cursor, faz query, aplica regra, formata resposta — tudo inline;
rotas com dezenas de linhas; SQL dentro do arquivo de rotas.
**Impacto:** viola MVC (controller magro/model gordo) e SRP; impossível reusar/testar a regra.
**Recomendação:** extrair regra para model/service; controller só orquestra; rota só mapeia.

### AP-07 — Callback Hell / Acoplamento sem separação (assíncrono aninhado) — **HIGH**
**O que é:** cadeias profundas de callbacks aninhados fazendo I/O sequencial, sem camadas.
**Sinais:** vários níveis de `db.get(... (err, x) => { db.run(... => { ... }) })`; `self = this`
para driblar escopo; lógica de transação espalhada em callbacks.
**Impacto:** ilegível, difícil tratar erro, propenso a bugs de fluxo; sem separação de camadas.
**Recomendação:** promisify/async-await; extrair repositório e service; transações explícitas.

### AP-08 — Query N+1 — **MEDIUM**
**O que é:** consulta dentro de loop, uma por item, em vez de uma consulta agregada/join.
**Sinais:** `for ... { SELECT ... WHERE id = ? }`; loop sobre resultados disparando nova query
para cada elemento (ex.: relatório que busca usuário e pagamento por matrícula, um a um).
**Impacto:** performance degrada linearmente com o volume; carga desnecessária no banco.
**Recomendação:** usar JOIN ou uma query com `IN (...)`; agregação no banco.

### AP-09 — Validação ausente nas rotas — **MEDIUM**
**O que é:** endpoints que confiam no input sem validar tipos, obrigatoriedade ou formato.
**Sinais:** `request.get_json()` usado direto sem checagem; ausência de schema (`marshmallow`/`joi`);
campos acessados sem verificar presença; conversões sem tratamento.
**Impacto:** erros 500, dados inconsistentes, superfície para abuso.
**Recomendação:** validação por schema na entrada; retornos 400 claros.

### AP-10 — Duplicação de código — **MEDIUM**
**O que é:** o mesmo trecho (montagem de resposta, query, validação) repetido em vários lugares.
**Sinais:** blocos copiados entre handlers; formatação de erro repetida; mesma query em N rotas.
**Impacto:** manutenção multiplicada, divergência silenciosa entre cópias.
**Recomendação:** extrair função/helper/model reutilizável (DRY).

### AP-11 — API deprecated / Uso de recurso obsoleto — **MEDIUM**
**O que é:** uso de APIs, métodos ou padrões marcados como obsoletos, com equivalente moderno.
**Como detectar:** confira a versão do framework/libs (Fase 1) e compare o uso com a documentação
atual da versão. Sinais comuns por ecossistema:
- Python/Flask: `@app.before_first_request` (removido no Flask 2.3+); `flask.Markup` (movido para
  `markupsafe`); `app.run()` em produção; `datetime.utcnow()` (deprecated em favor de
  `datetime.now(timezone.utc)`).
- Node/Express: `body-parser` avulso quando `express.json()` já existe; `crypto.createCipher`
  (use `createCipheriv`); `new Buffer()` (use `Buffer.from`); callbacks onde a lib já oferece Promises.
- Geral: métodos marcados `@deprecated`, libs sem manutenção, sintaxe de versão anterior.
**Impacto:** quebra em upgrades futuros; perde correções de segurança/performance da versão nova.
**Recomendação:** substituir pelo equivalente moderno documentado (cite qual).
> A detecção de APIs deprecated é **obrigatória** na auditoria — sempre verifique este item.

### AP-12 — Recursos vazando / Falta de tratamento transacional — **MEDIUM**
**O que é:** operações relacionadas que deveriam ser atômicas feitas sem transação, ou recursos
não liberados; deleção que deixa dados órfãos.
**Sinais:** `DELETE FROM users` sem limpar dependências (matrículas/pagamentos ficam órfãos);
múltiplos `INSERT` relacionados sem transação; conexões/arquivos não fechados.
**Impacto:** inconsistência de dados, integridade referencial quebrada.
**Recomendação:** transações; cascata explícita; liberação de recursos (context manager/finally).

### AP-13 — Endpoint perigoso exposto sem proteção — **CRITICAL**
**O que é:** rotas administrativas destrutivas sem autenticação/autorização.
**Sinais:** `/admin/reset-db` que apaga tabelas; `/admin/query` que roda SQL; delete em massa
sem checagem de permissão.
**Impacto:** qualquer um pode destruir ou ler todo o banco.
**Recomendação:** remover ou proteger com auth/role; jamais expor SQL arbitrário.

### AP-14 — Magic numbers / Strings mágicas — **LOW**
**O que é:** números/valores literais sem nome, com significado de negócio.
**Sinais:** `preco * 1.1`, `status == 2`, `timeout 3600`, taxas/limites soltos no meio do código.
**Impacto:** intenção obscura, mudança arriscada, duplicação de valores.
**Recomendação:** extrair para constantes nomeadas em config ou no topo do módulo.

### AP-15 — Nomenclatura ruim / Baixa legibilidade — **LOW**
**O que é:** nomes de variáveis/funções não descritivos, abreviações crípticas, inconsistência.
**Sinais:** `u`, `e`, `p`, `cc`, `cid`; funções que não dizem o que fazem; mistura de idiomas.
**Impacto:** curva de leitura maior, mais bugs por mal-entendido.
**Recomendação:** renomear para nomes intencionais e consistentes.

### AP-16 — Debug/verbosidade em produção — **LOW/MEDIUM**
**O que é:** modo debug ligado, `print`/`console.log` de dados sensíveis, stack traces expostos.
**Sinais:** `DEBUG = True`, `debug=True` no `run`, `console.log` de cartão/senha/chave.
**Impacto:** vazamento de informação, superfície de ataque (LOW se cosmético; MEDIUM se vaza dado sensível).
**Recomendação:** controlar por ambiente; logging estruturado sem dados sensíveis.

---

## Cobertura mínima e distribuição

- Este catálogo tem **16 anti-patterns** cobrindo as 4 severidades (CRITICAL: AP-01..04, AP-13;
  HIGH: AP-05..07; MEDIUM: AP-08..12, AP-16; LOW: AP-14, AP-15).
- Sempre inclua a checagem de **APIs deprecated (AP-11)**.
- Cruze com `04-mvc-guidelines.md` para gerar os findings de **aderência a MVC** (o que está fora
  de cada camada, com arquivo e linhas).
