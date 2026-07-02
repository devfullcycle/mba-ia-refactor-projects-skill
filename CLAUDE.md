# CLAUDE.md

Este arquivo fornece orientações ao Claude Code (claude.ai/code) ao trabalhar com código neste repositório.

## O que é este repositório

Este é um repositório de desafio de MBA ("Criação de Skills — Refatoração Arquitetural Automatizada", ver [PLANEJAMENTO.md](PLANEJAMENTO.md) para o texto original do desafio). O entregável **não** é código de aplicação — é uma Skill do Claude Code chamada `refactor-arch` que analisa qualquer codebase de backend, audita contra um catálogo de anti-patterns e refatora para o padrão MVC. O repositório contém três projetos de exemplo intencionalmente bagunçados, contra os quais a skill precisa rodar com sucesso.

```
code-smells-project/     Python/Flask — API de e-commerce, monolito em arquivo único (app.py/controllers.py/models.py/database.py)
ecommerce-api-legacy/    Node.js/Express — API de LMS com fluxo de checkout, God class em AppManager.js
task-manager-api/        Python/Flask — task manager, parcialmente organizado (models/, routes/, services/, utils/) mas ainda com falhas
reports/                 Saída da auditoria (Fase 2) de cada projeto (audit-project-1.md, -2.md, -3.md)
```

Cada um dos três diretórios de projeto é uma aplicação autocontida, com seu próprio `README.md`, manifesto de dependências e (após criada) sua própria cópia de `.claude/skills/refactor-arch/` — a skill precisa ser portável por copiar-e-colar entre os três, então nada dentro dela pode assumir a estrutura de arquivos de um projeto específico.

## A skill: `.claude/skills/refactor-arch/`

Vive primeiro dentro de `code-smells-project/`, depois é copiada literalmente para a raiz dos outros dois projetos. Estrutura obrigatória:

- `SKILL.md` — o ponto de entrada/prompt, conduz 3 fases sequenciais (nome e ordem das fases são fixos pelo enunciado, não renomear)
- Arquivos de referência em markdown cobrindo 5 áreas de conhecimento (nomes/quantidade de arquivos são livres, mas cada área precisa estar coberta por algo):
  1. Heurísticas de análise de projeto (detecção de linguagem/framework/DB/arquitetura)
  2. Catálogo de anti-patterns — mín. 8 itens, cada um com sinais de detecção + severidade, deve incluir detecção de APIs deprecated
  3. Template de relatório de auditoria (formato de saída da Fase 2)
  4. Guidelines de arquitetura MVC (responsabilidades de Models / Views-Routes / Controllers)
  5. Playbook de refatoração — mín. 8 padrões de transformação com exemplo antes/depois

### Contrato das fases (não desviar)

1. **Fase 1 — Análise**: detecta linguagem/framework/dependências/domínio/arquitetura, imprime um resumo. Nenhuma alteração de arquivo.
2. **Fase 2 — Auditoria**: cruza o código contra o catálogo de anti-patterns, gera um relatório de findings (arquivo + linhas exatas, ordenado CRITICAL→LOW), **então para e pede confirmação explícita do usuário** antes de tocar em qualquer coisa. Essa pausa é um requisito obrigatório, não uma opção de UX.
3. **Fase 3 — Refatoração**: reestrutura para MVC, depois valida — a aplicação precisa subir sem erros e os endpoints originais precisam continuar respondendo. Só prossegue após a confirmação da Fase 2.

### Escala de severidade (fixa, usar exatamente esta rubrica)

- **CRITICAL**: falhas graves de arquitetura/segurança que quebram o funcionamento correto ou expõem dados — credenciais hardcoded, SQL injection, "God Class" misturando banco de dados + lógica de negócio + roteamento
- **HIGH**: violações fortes de MVC/SOLID que dificultam muito manutenção/testabilidade — lógica de negócio presa em controllers, forte acoplamento sem injeção de dependência, estado global mutável
- **MEDIUM**: problemas de padronização/duplicação/performance moderada — queries N+1, uso inadequado de middleware, validação ausente nas rotas
- **LOW**: legibilidade, nomenclatura, magic numbers

### Critério de aceite (precisa valer para os 3 projetos de exemplo, não apenas um)

- Fase 1 identifica a stack corretamente
- Fase 2 encontra >= 5 findings, com pelo menos 1 CRITICAL ou HIGH
- Fase 3 deixa a aplicação subindo e todos os endpoints originais respondendo

## Como rodar cada projeto de exemplo

```bash
# code-smells-project (Flask, porta 5000, SQLite loja.db criado automaticamente com dados de seed)
cd code-smells-project && pip install -r requirements.txt && python app.py

# ecommerce-api-legacy (Express, porta 3000, SQLite em memória, seed carregado no boot)
cd ecommerce-api-legacy && npm install && npm start
# exemplos de requisições em ecommerce-api-legacy/api.http

# task-manager-api (Flask, porta 5000, SQLite tasks.db — precisa rodar o seed ANTES do primeiro boot ou os endpoints retornam listas vazias)
cd task-manager-api && pip install -r requirements.txt && python seed.py && python app.py
```

Invocar a skill já instalada em um projeto: `claude "/refactor-arch"` a partir da raiz do projeto.

## Arquitetura conhecida dos projetos de exemplo (contexto para a análise manual e para as heurísticas de detecção da skill)

- **code-smells-project**: `app.py` conecta as rotas diretamente via `add_url_rule` a funções em `controllers.py`; `controllers.py` contém lógica de negócio + chamadas para `models.py`; `models.py` contém SQL cru contra o `get_db()` de `database.py`. Pontos de atenção: `SECRET_KEY` hardcoded, `debug=True`, um endpoint `/admin/query` que executa SQL arbitrário vindo do corpo da requisição, e um `/admin/reset-db` sem autenticação.
- **ecommerce-api-legacy**: `src/app.js` é um bootstrap enxuto; `src/AppManager.js` é uma God class que possui a conexão com o banco, criação de schema, dados de seed e todos os handlers de rota (pirâmides de callbacks profundamente aninhadas em `/api/checkout` e `/api/admin/financial-report`); `src/utils.js` contém helpers transversais, incluindo `badCrypto` (hash de senha fraco) e uma chave de gateway de pagamento.
- **task-manager-api**: já possui `models/`, `routes/` (blueprints do Flask), `services/`, `utils/` — mais próximo de uma organização em camadas, mas as rotas ainda contêm lógica de negócio e queries diretas via SQLAlchemy, em vez de delegar de forma consistente para os services; vale checar `services/notification_service.py` e `utils/helpers.py` quanto a responsabilidades fora de lugar. Este projeto é o caso de teste "parcialmente organizado" — a skill precisa encontrar problemas reais e melhorar a estrutura sem assumir uma reescrita do zero.

## Convenções de trabalho neste repositório

- Os achados da análise manual entram no [README.md](README.md) da raiz, na seção "Análise Manual" — não em comentários de código ou documentos separados.
- Os relatórios de auditoria (saída da Fase 2) são salvos em `reports/audit-project-{1,2,3}.md`, um por projeto, e são a saída literal da execução da skill — não escrever esses relatórios manualmente.
- O código refatorado é commitado no próprio diretório de cada projeto, não copiado para outro lugar.
- Ao iterar nos arquivos de referência da skill depois de uma execução abaixo do esperado (poucos findings, refatoração quebrando a aplicação), ajustar os arquivos de referência em markdown e rodar novamente — o próprio enunciado do desafio prevê de 2 a 4 iterações por projeto.
