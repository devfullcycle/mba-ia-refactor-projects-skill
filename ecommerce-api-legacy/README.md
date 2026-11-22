# ecommerce-api-legacy

LMS API (com fluxo de checkout: cursos, matrículas, pagamentos e relatório financeiro) em Node.js/Express, refatorada para MVC em camadas pela skill `refactor-arch` (`.claude/skills/refactor-arch/`).

> Status: skill executada neste projeto (3 fases concluídas e validadas).

---

## A) Análise Manual

Li o código original inteiro (`app.js`, `AppManager.js` e `utils.js`, uns 180 linhas) antes de rodar a skill e anotei o que mais me chamou atenção. Usei estes critérios de severidade:

- **CRITICAL:** falha grave de segurança ou arquitetura, como credencial hardcoded e "God Class" com banco, lógica e roteamento no mesmo arquivo.
- **HIGH:** violação forte de MVC ou SOLID que complica a manutenção e os testes, como acoplamento sem injeção de dependência, estado global mutável e ausência de camadas.
- **MEDIUM:** problemas de padronização, duplicação e performance moderada, como validações ausentes e tratamento de erros espalhado.
- **LOW:** legibilidade, nomes ruins e magic numbers.

| # | Severidade | O que encontrei | Onde | Por que incomoda |
|---|---|---|---|---|
| 1 | CRITICAL | **Valores sensíveis hardcoded.** Senha do banco, chave live do gateway de pagamento e usuários de serviço estão escritos direto no código. | `utils.js` 2-5 | É um risco de segurança, pois expõe dados sensíveis: quem tem acesso ao repositório já tem as credenciais. |
| 2 | CRITICAL | **Um arquivo gigante com todas as responsabilidades.** A classe `AppManager` cria o banco, define schema e seed, registra as rotas, executa o SQL, aplica a regra do checkout e monta as respostas. | `AppManager.js` 4-139 | Baixa manutenibilidade e alto esforço cognitivo para entender o código. Qualquer mudança gera riscos altos e difíceis de prever. |
| 3 | HIGH | **Alto acoplamento.** O `AppManager` cria a própria conexão com o banco, as rotas usam o driver direto, e `utils.js` exporta um cache e um contador globais mutáveis. Nada é injetado. | `AppManager.js:7`, `app.js:8`, `utils.js` 9-15 | Baixa manutenibilidade e alto esforço cognitivo para entender o código. Qualquer mudança gera riscos altos e difíceis de prever. |
| 4 | HIGH | **Projeto não estruturado.** Não existem camadas: a regra de pagamento, as consultas e a serialização ficam dentro dos handlers das rotas, com até 7 níveis de callbacks aninhados. | `AppManager.js` 28-129 | Ninguém sabe onde termina a rota, a regra e o acesso a dados. O checkout ainda cria o usuário antes de validar o pagamento. |
| 5 | MEDIUM | **Validação de entrada fraca.** No checkout só se checa a presença dos campos: não há validação de formato do e-mail, do tipo do `c_id` nem do cartão, e a senha é opcional (cai em uma senha padrão). O `:id` do `DELETE` também não é validado. | `AppManager.js` 29-35, 132 | Dados inválidos entram no sistema e contas são criadas com senha previsível. |
| 6 | MEDIUM | **[AP-11] Tratamento de erros ausente ou espalhado.** Erros do banco são ignorados em vários pontos (o erro da consulta de matrículas nem é checado antes de usar o resultado), e o `DELETE` sempre responde sucesso. Cada rota monta a própria resposta de erro, sem um tratador central. | `AppManager.js` 57-61, 92-93, 104-106, 133-135 | Falhas ficam silenciosas ou derrubam o processo, e o formato das respostas de erro é inconsistente. |
| 7 | LOW | **Nomes de classes, métodos e variáveis ruins.** Variáveis como `u`, `e`, `p`, `cid`, `cc`, `c` e `enr`, uma função chamada `badCrypto` e uma classe genérica `AppManager`. | `AppManager.js` 29-33, 90, 102, `utils.js:17` | A intenção do código fica escondida e a leitura exige adivinhar o que cada nome significa. |
| 8 | LOW | **Magic numbers e strings soltas.** `"PAID"`, `"DENIED"`, o prefixo `"4"` do cartão, a senha padrão `"123456"`, e o 10000 e o 10 dentro de `badCrypto`. | `AppManager.js` 46, 48, 68, `utils.js` 19, 22 | Fica difícil achar e mudar essas regras, e o significado dos valores não está escrito em lugar nenhum. |

No total são 8 problemas: 2 CRITICAL, 2 HIGH, 2 MEDIUM e 2 LOW.


---

## B) Construção da Skill

### Processo

1. **Estudo da base.** Li os resumos das aulas do MBA e a documentação oficial: [Skills no Claude Code](https://code.claude.com/docs/en/skills), o [Complete Guide to Building Skills](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf) e o artigo [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/research/equipping-agents-for-the-real-world-with-agent-skills). Desse estudo saiu um guia próprio (`como-construir-uma-skill.md`) e um template de skill.
2. **Decisões de design a partir do guia.**
   - Divisão em `SKILL.md` enxuto + `references/` + `assets/` + `scripts/`, com *progressive disclosure*: o `SKILL.md` traz o fluxo e as regras, e os detalhes só são lidos quando a fase precisa deles.
   - `disable-model-invocation: true`, porque a skill altera o projeto e só deve rodar quando invocada com `/refactor-arch`.
   - Um script (`scan.sh`) só para o que é determinístico e barato (inventário, arquivos grandes, padrões textuais). O julgamento fica com o modelo.
   - A pausa da Fase 2 é regra inviolável: Fases 1 e 2 são somente leitura e a Fase 3 só começa após `y`.
3. **Primeira versão.** Estrutura em 3 fases (análise, auditoria com relatório e confirmação, refatoração MVC com validação), catálogo de 16 anti-patterns (AP-01 a AP-16, incluindo APIs deprecated), playbook com 12 padrões antes/depois (PB-01 a PB-12), diretrizes de MVC e template de relatório.
4. **Refatoração para agnosticismo de tecnologia.** A primeira versão tinha exemplos presos a linguagens específicas. Reescrevi o catálogo, o playbook e o `scan.sh` com sinais conceituais e pseudocódigo neutro. Depois de detectar a stack por evidência (manifesto, extensões, imports), a skill pesquisa as boas práticas e as APIs deprecated daquela linguagem e versão e monta um Stack Profile interno. Esse perfil alimenta a auditoria e a tradução dos padrões para a forma idiomática da stack. O que não tem fonte é marcado como "a verificar". A pesquisa usa só tecnologia, versão e tema, nunca dados do projeto.
5. **Organização conforme a documentação.** O template do relatório saiu de `references/` e foi para `assets/`, já que é um arquivo usado na saída e não material de consulta.
6. **Ajuste do formato de saída.** Nos testes, as Fases 1 e 2 imprimiam informação extra (Stack Profile, tabela de endpoints, seções de deprecated, plano de refatoração, perguntas antes da confirmação). Passei a tratar esse conteúdo como interno e a exigir a saída exatamente no formato esperado, sem seções adicionais. Decisões pendentes (ex.: migração de senhas) ficam para a Fase 3, registradas em "Deviations" e "Needs Human".

### Estrutura final da skill

```
.claude/skills/refactor-arch/
├── SKILL.md                         # fluxo das 3 fases + regras inviolantes
├── references/
│   ├── project-analysis.md          # como detectar stack, banco, domínio e arquitetura
│   ├── stack-research.md            # pesquisa de boas práticas da stack (Stack Profile)
│   ├── anti-patterns-catalog.md     # AP-01..AP-16 com severidade e sinais
│   ├── mvc-guidelines.md            # camadas, regra de dependência, estrutura-alvo
│   └── refactoring-playbook.md      # PB-01..PB-12 antes/depois em pseudocódigo
├── assets/
│   └── report-template.md           # template do relatório da Fase 2
└── scripts/
    └── scan.sh                      # inventário e candidatos a anti-patterns
```

### Principais regras de projeto da skill

- Nenhum arquivo é alterado antes da confirmação da Fase 2.
- Todo finding cita arquivo e linha exatos, e segredos aparecem mascarados.
- O contrato externo (rotas, status, formato) é preservado, e mudanças deliberadas são registradas como Deviations.
- Não há sucesso declarado sem build/boot e comparação dos endpoints com o baseline, com no máximo 3 tentativas de correção.
- Afirmações sobre deprecations ou práticas sem fonte são marcadas como "a verificar".

---

## C) Resultados

Relatório de auditoria (saída da Fase 2): [audit-project-2.md](../reports/audit-project-2.md).

### Resumo do relatório de auditoria

| CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|
| 3 | 4 | 5 | 3 | **15** |

Principais achados: God Class `AppManager` com rotas, SQL e regra no mesmo arquivo (AP-01), credenciais e chave live do gateway hardcoded (AP-02), "hash" de senha caseiro e rotas administrativas/destrutivas sem autenticação (AP-04), número do cartão logado em texto (AP-08), N+1 no relatório financeiro (AP-09) e erros de banco ignorados (AP-11).

Neste projeto a skill gerou um finding AP-13: o estilo de callbacks aninhados (até 7 níveis) do `sqlite3`, com substituto `async/await`. Não foi encontrada nenhuma API do Express 4.18 deprecated. A pesquisa da stack ficou "partially verified" (3 fontes consultadas), e o status oficial de deprecation do padrão de callbacks do `sqlite3` ficou como "a verificar".

Não houve finding de SQL Injection: todas as queries originais já usavam placeholders.

### Comparação antes/depois da estrutura

Antes (monolítico, 3 arquivos, ~180 linhas):

```
ecommerce-api-legacy/
├── src/
│   ├── app.js          # cria o servidor e instancia o AppManager
│   ├── AppManager.js   # 141 linhas: banco, schema/seed, rotas, regra de checkout, SQL, serialização
│   └── utils.js        # config com segredos + cache global + "criptografia" caseira
├── api.http
└── package.json
```

Depois (MVC em camadas, 26 arquivos em `src/`):

```
ecommerce-api-legacy/
├── src/
│   ├── app.js          # composition root (mesmo comando: npm start)
│   ├── config/         # index.js (env) + constants.js
│   ├── database/       # Database.js (adaptador de promessas), schema.js (schema + seed)
│   ├── models/         # user, course, enrollment, payment, auditLog, financialReport
│   ├── services/       # checkout, financialReport, user, password (scrypt), paymentGateway
│   ├── controllers/    # checkout, admin, user
│   ├── routes/         # index.js
│   ├── middlewares/    # adminAuth, asyncHandler, errorHandler
│   ├── validators/     # checkoutValidator.js
│   ├── errors/         # AppError.js
│   └── utils/          # logger.js
├── .env.example  .gitignore  api.http  package.json  README.md
```

Mapeamento MVC: Model → `models/` (com `database/`), Controller → `controllers/` (com regras em `services/`), View/Routes → `routes/`.

### Mudanças deliberadas de comportamento (Deviations)

- `GET /api/admin/financial-report` e `DELETE /api/users/:id` agora exigem o header `x-admin-token`: 401 sem o token ou com token errado, 403 se `ADMIN_TOKEN` não estiver configurado.
- Novo usuário sem `pwd` no checkout retorna 400 "Bad Request" (antes recebia a senha padrão `123456`). Usuário já existente continua sem precisar de senha.
- Pagamento recusado não cria mais o usuário (antes ele era criado antes de validar o pagamento).
- Entradas inválidas que antes geravam exceção, 404 ou 200 (e-mail malformado, `card` que não é string, JSON malformado, `:id` não inteiro) agora retornam 400 "Bad Request".
- Erros de banco retornam 500 "Erro interno" (antes mensagens como "Erro DB" ou "Erro Matrícula", falha silenciosa ou queda do processo).
- A ordem dos alunos no relatório agora é determinística (por id da matrícula). No legado dependia da ordem de conclusão assíncrona.
- Logs mudaram de formato e deixam de conter cartão e chave do gateway. O cache `last_checkout_*`, que era escrito e nunca lido, foi removido.
- A senha do usuário seed deixou de ser `123`: recebe uma senha aleatória descartada (não existe endpoint de login).

### Pendências que exigem decisão humana

- Rotacione a chave do gateway (`pk_l****`) e as demais credenciais expostas: elas continuam no histórico git dos commits anteriores.
- Defina `ADMIN_TOKEN` e decida o modelo real de autenticação e autorização (hoje é um token compartilhado, não uma identidade por usuário).
- `DELETE /api/users/:id` continua deixando matrículas e pagamentos órfãos (comportamento e mensagem preservados). Decida entre cascata e soft delete.
- O checkout não usa transação: usuário, matrícula e pagamento podem ficar parciais se um insert falhar.
- O projeto não tem suíte de testes automatizados.
- O código refatorado ainda não foi commitado.

### Checklist de validação

```markdown
### Fase 1 — Análise
- [x] Linguagem detectada corretamente (JavaScript / Node.js)
- [x] Framework detectado corretamente (Express ^4.18.2)
- [x] Domínio da aplicação descrito corretamente (LMS com checkout, matrículas, pagamentos e relatório financeiro)
- [x] Número de arquivos analisados condiz com a realidade (3)

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (15)
- [x] Detecção de APIs deprecated incluída (AP-13: callbacks aninhados; nenhuma API deprecated do Express)
- [x] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída para módulo de config (sem hardcoded)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para visualização ou roteamento
- [x] Controllers concentram o fluxo da aplicação (regras em services/)
- [x] Error handling centralizado
- [x] Entry point claro
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente (3/3, com as diferenças listadas em Deviations)
```

### Logs da aplicação rodando após a refatoração

Boot (com `ADMIN_TOKEN` definido):

```
[2026-11-21T23:45:21.201Z] [INFO] Frankenstein LMS rodando na porta 3000...
```

Boot sem `ADMIN_TOKEN` (rotas administrativas bloqueadas):

```
[2026-11-21T23:45:32.956Z] [INFO] Frankenstein LMS rodando na porta 3000...
[2026-11-21T23:45:32.958Z] [WARN] ADMIN_TOKEN não definido: rotas administrativas estão bloqueadas (403).
```

As mesmas chamadas foram feitas no app original (baseline) e no refatorado, e as respostas foram comparadas. Resultado do app refatorado:

```
POST   /api/checkout (cartão 4111..., curso 2)       -> 200 {"msg":"Sucesso","enrollment_id":2}
POST   /api/checkout (cartão 5111..., recusado)      -> 400 Pagamento recusado
POST   /api/checkout (corpo incompleto)              -> 400 Bad Request
POST   /api/checkout (curso inexistente)             -> 404 Curso não encontrado
POST   /api/checkout (usuário existente, sem pwd)    -> 200 {"msg":"Sucesso","enrollment_id":3}
POST   /api/checkout (usuário novo, sem pwd)         -> 400 Bad Request   (antes: senha padrão)
GET    /api/admin/financial-report (sem token)       -> 401               (antes: 200)
GET    /api/admin/financial-report (com token)       -> 200 (mesmo JSON do original)
DELETE /api/users/1 (sem token)                      -> 401               (antes: 200)
DELETE /api/users/1 (com token)                      -> 200 "Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."
GET    /api/admin/financial-report (após o delete)   -> 200 (aluno "Unknown", como no original)
```

Com `ADMIN_TOKEN` ausente, as duas rotas administrativas retornam 403. JSON malformado e cartão numérico retornam 400.

O relatório financeiro ficou idêntico ao original: `Clean Architecture` com receita 997 e `Docker` com receita 994, mesmos alunos e valores pagos. A única diferença é a ordem dos alunos, que agora é fixa.

O re-scan com `scan.sh` não deixou anti-patterns: os 4 candidatos restantes (nome de header, literal `0` em comparação, comentário e SQL estático) são falsos positivos e foram descartados lendo o código.

Não há screenshots. A validação foi feita por logs e requisições HTTP.

### Observações sobre o comportamento da skill

- **Detecção e baseline:** a skill detectou Node.js/Express e SQLite pelo `package.json` e pelos `require`, identificou o domínio de LMS pelos nomes das tabelas e rotas, e mapeou os 3 endpoints como baseline antes de alterar qualquer arquivo. O baseline foi capturado rodando o app legado e depois comparado com o refatorado.
- **Pesquisa da stack:** foram 3 consultas, com verificação parcial. As fontes confirmaram o guia de segurança e de tratamento de erros do Express, mas não trouxeram uma lista oficial de deprecations do Express 4.18. Por isso nenhuma deprecation foi afirmada sem fonte, e o ponto do `sqlite3` ficou como "a verificar".
- **Diferença em relação à stack Python:** no Node a skill traduziu os padrões para `async/await`, injeção por construtor e middlewares do Express (incluindo um `asyncHandler`, já que o Express 4 não encaminha rejeições de handlers assíncronos), e usou `crypto.scrypt` nativo para o hash de senha em vez de adicionar dependência.
- **Contrato preservado:** o formato de erro em texto puro da API original foi mantido no tratador central, em vez de trocá-lo por JSON.

---

## D) Como Executar

### Pré-requisitos

- **Claude Code** instalado e autenticado (`claude --version`).
- Node.js 20+ e `npm`.
- A skill em `.claude/skills/refactor-arch/` (já presente neste projeto).
- Opcional: `bash` no PATH, usado pelo script auxiliar `scan.sh`. Sem ele a skill usa Glob/Grep.

### Executando a skill

```bash
cd ecommerce-api-legacy
claude "/refactor-arch"
```

A skill imprime o resumo da Fase 1 e o relatório da Fase 2, e então pergunta `Proceed with refactoring (Phase 3)? [y/n]`. Responda `y` para refatorar. Nada é alterado antes disso.

### Como rodar este projeto

```bash
npm install
ADMIN_TOKEN="<defina um valor longo e aleatório>" npm start   # ADMIN_TOKEN é opcional: sem ele as rotas admin respondem 403
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds (um usuário, dois cursos, uma matrícula e um pagamento) a cada boot. As variáveis de ambiente (`PORT`, `DATABASE_FILE`, `ADMIN_TOKEN`) estão em [.env.example](.env.example). As rotas `GET /api/admin/financial-report` e `DELETE /api/users/:id` exigem o header `x-admin-token`. Exemplos de requisições estão em [api.http](api.http).

### Como validar que a refatoração funcionou

```bash
# com a aplicação rodando (ADMIN_TOKEN=segredo), em outro terminal
curl -s -X POST localhost:3000/api/checkout -H "Content-Type: application/json" \
     -d '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'   # 200
curl -s -X POST localhost:3000/api/checkout -H "Content-Type: application/json" \
     -d '{"usr":"Joao","eml":"joao@teste.com","pwd":"123","c_id":1,"card":"5111222233334444"}'                    # 400 Pagamento recusado
curl -s localhost:3000/api/admin/financial-report                                                                   # 401 (sem token)
curl -s localhost:3000/api/admin/financial-report -H "x-admin-token: segredo"                                       # 200
```

Checklist rápido:

1. A aplicação inicia sem erros com o comando de antes (`npm start`).
2. Cada rota do baseline responde com o mesmo status e formato (diferenças só as de "Mudanças deliberadas de comportamento").
3. Nenhum segredo no código e nenhuma query concatenada: `grep -rnE "pk_live|senha_super|SELECT .*\+" src` não deve retornar nada.
4. O relatório de auditoria está em `../reports/audit-project-2.md`.
