# Criação de Skills - Refatoração Arquitetural Automatizada com Claude Code
## MBA em Engenharia de Software com IA - FullCycle

**Repositório de entrega no GitHub:**
  - [ivanaugustineli/mba-ia-refactor-projects-skill](https://github.com/ivanaugustineli/mba-ia-refactor-projects-skill)

---
## 📌 Visão Geral do Projeto

Neste projeto desafio, foi criada uma Skill que automatiza o processo de revisão e correção de projetos legados com problemas de arquitetura, segurança e qualidade de código, analisando, auditando e refatorando qualquer projeto para o padrão MVC, independente da tecnologia.

---

## 📝 *Análise Manual*

- Lista dos problemas identificados manualmente em cada projeto
- Classificação por severidade
- Justificativa de por que cada problema é relevante

  ### 📂 **code-smells-project**
  - SQL construído por concatenação de strings em todo o `models.py` (vulnerável a SQL Injection).
  - Senhas armazenadas em texto puro.
  - Conexão global única ao banco `check_same_thread=False`.
  - Endpoint `/admin/query` que executa SQL arbitrário sem autenticação.
  - `secret_key` hardcoded e exposta no `/health`.
  - Lógica de notificação (email/SMS/push) embutida diretamente no controller como `print()`.
  - Duplicação massiva de código entre `get_pedidos_usuario` e `get_todos_pedidos`.
  - Queries N+1 ao carregar itens dos pedidos.

    ### *Lista por Severidade e Justificativa*

    | # | Severidade | Tipo de Problema | Justificativa |
    |---|---|---|---|
    | 1 | 🔴 CRITICAL| **SQL Injection** | Queries construídas por concatenação de string em toda a camada de dados, possibilitanto injeção de códigos maliciósos. | 
    | 2 | 🔴 CRITICAL | **Secret key hardcoded** | Chave exposta diretamente no código-fonte. |
    | 3 | 🔴 CRITICAL | **Secret key exposta na resposta HTTP** | Campo `secret_key` devolvido no JSON do `/health` expondo a chave da API.|
    | 4 | 🔴 CRITICAL | **Endpoint admin sem autenticação** | `/admin/reset-db` apaga todo o banco sem qualquer verificação de identidade. |
    | 5 | 🔴 CRITICAL | **Endpoint admin sem autenticação** | `/admin/query` executa SQL arbitrário sem autenticação, permitindo acesso irrestrito ao banco. |
    | 6 | 🔴 CRITICAL | **Senha em texto puro** | Armazenada no banco e comparada diretamente sem hash. |
    | 7 | 🔴 CRITICAL | **Dados sensíveis expostos na API** | Senha retornada no payload de resposta de usuário. |
    | 8 | 🟠 HIGH | **Lógica de negócio no Controller** | Notificações de email/SMS/push embutidas diretamente no handler HTTP, violando separação MVC. |
    | 9 | 🟠 HIGH | **Lógica de negócio no Controller** | Notificações de mudança de status de pedido embutidas no handler, sem camada de serviço. |
    | 10 | 🟠 HIGH | **Conexão global mutável ao banco** | Singleton com `check_same_thread=False` e sem gestão de ciclo de vida, estado global compartilhado por toda a aplicação. |
    | 11 | 🟠 HIGH | **Validação de domínio no Controller** | Regras de negócio (tamanho de nome, categorias válidas, preço negativo) presas no handler HTTP sem camada de validação separada. |
    | 12 | 🟡 MEDIUM | **Código duplicado** | `get_pedidos_usuario` e `get_todos_pedidos` são idênticos exceto pelo filtro de `usuario_id`. |
    | 13 | 🟡 MEDIUM | **Queries N+1** | Para cada pedido, dispara queries separadas para itens e depois para cada produto individualmente. |
    | 14 | 🟡 MEDIUM | **Validação duplicada** | Bloco de validação de produto copiado entre `criar_produto` e `atualizar_produto` sem reaproveitamento. |
    | 15 | 🟡 MEDIUM | **Informações de infraestrutura expostas** | `db_path`, `ambiente` e `debug` retornados pelo `/health` em produção. |
    | 16 | 🔵 LOW | **`DEBUG=True` hardcoded** | Modo debug ativado no código, deveria ser controlado por variável de ambiente. |
    | 17 | 🔵 LOW | **`host="0.0.0.0"` hardcoded** | Servidor exposto em todas as interfaces sem configuração externa. |
    | 18 | 🔵 LOW | **`print()` como logging** | Sem níveis de log, sem timestamp, sem rastreabilidade estruturada |

  ### 📂 **ecommerce-api-legacy**
  - Classe `AppManager` concentra banco de dados, rotas, regras de negócio e logs tudo junto.
  - Chave de gateway de pagamento, senha de SMTP e senha de DB expostas em `utils.js`.
  - Função `badCrypto` que apenas faz base64 em loop - não é hash seguro.
  - Relatório financeiro dispara múltiplas queries aninhadas para cada curso/matrícula.
  - O endpoint admin é totalmente aberto.
  - Deleção de usuário sem remover registros relacionados.
  - Estado compartilhado em variável global `globalCache`.

    ### *Lista por Severidade e Justificativa*

    | # | Severidade | Tipo de Problema | Justificativa |
    |---|---|---|---|
    | 1 | 🔴 CRITICAL | **Credenciais hardcoded** | Senha de DB, chave do gateway de pagamento e usuário SMTP expostos no código. |
    | 2 | 🔴 CRITICAL | **God Class** | `AppManager` acumula conexão com banco, schema, seeds, rotas e regras de negócio, violando completamente a separação de responsabilidades. |
    | 3 | 🔴 CRITICAL | **Criptografia fraca** | `badCrypto` usa base64 em loop como substituto de hash, sem salt e sem algoritmo seguro, expondo senhas de usuários. |
    | 4 | 🔴 CRITICAL | **Chave de gateway e cartão expostos em log** | Número do cartão e chave de produção são printados no console durante o checkout. |
    | 5 | 🟠 HIGH | **Sem autenticação no endpoint admin** | `/api/admin/financial-report` é totalmente público, sem nenhuma verificação de identidade ou permissão. |
    | 6 | 🟠 HIGH | **Estado global mutável** | `globalCache` e `totalRevenue` são variáveis globais de módulo compartilhadas por toda a aplicação, sem controle de acesso. |
    | 7 | 🟠 HIGH | **Lógica de negócio no roteamento** | Regras de checkout (criar usuário, processar pagamento, matricular) estão todas embutidas diretamente no handler da rota. |
    | 8 | 🟡 MEDIUM | **N+1 queries** - Relatório financeiro dispara queries aninhadas para cada curso, matrícula, usuário e pagamento sem nenhum JOIN. |
    | 9 | 🟡 MEDIUM | **Deleção sem integridade referencial** | `DELETE /api/users/:id` remove o usuário mas deixa matrículas e pagamentos órfãos no banco. |
    | 10 | 🟡 MEDIUM | **Erros de DB silenciados** | Callbacks de query sem checagem de `err` no relatório financeiro, podendo mascarar falhas silenciosamente. |
    | 11 | 🔵 LOW | **Senha em texto puro nos seeds** | Usuário seed inserido com senha `'123'` sem hash. |
    | 12 | 🔵 LOW | **Nomenclatura de variáveis ruim** | Parâmetros do checkout usam abreviações opacas (`u`, `e`, `p`, `cid`, `cc`) sem nenhuma semântica clara. |

  ### 📂 **task-manager-api**
  - Lógica de negócio (`is_overdue`) duplicada em múltiplos lugares (routes, models).
  - `to_dict()` do `User` expõe o hash da senha.
  - Senha armazenada com MD5 (inseguro).
  - `NotificationService` tem credenciais hardcoded e estado em memória.
  - Login retorna um "token" falso sem autenticação real.
  - Validações duplicadas entre routes e `helpers.py`.
  - Imports não utilizados espalhados pelo código.
  - Ausência de testes automatizados.

    ### *Lista por Severidade e Justificativa*

    | # | Severidade | Tipo de Problema | Justificativa |
    |---|---|---|---|
    | 1 | 🔴 CRITICAL | **Credenciais hardcoded** | Usuário e senha de e-mail escritos no código-fonte. |
    | 2 | 🔴 CRITICAL | **Secret key hardcoded** | Chave secreta do Flask no código-fonte. |
    | 3 | 🔴 CRITICAL | **Hashing inseguro** | Senha armazenada com MD5 (quebrável, não é KDF). |
    | 4 | 🔴 CRITICAL | **Exposição de dado sensível** | `to_dict()` serializa o hash da senha na resposta HTTP. |
    | 5 | 🔴 CRITICAL | **Token de autenticação falso** | Login retorna string fixa sem JWT ou sessão real. |
    | 6 | 🟠 HIGH | **Lógica de negócio no controller** | Cálculo de `overdue` duplicado nas routes em vez de delegar ao model. |
    | 8 | 🟠 HIGH | **Lógica de negócio no controller** | Mesmo cálculo de `overdue` repetido nos relatórios. |
    | 9 | 🟠 HIGH | **Método do model ignorado** | `Task.is_overdue()` existe mas as routes nunca o chamam (violação MVC). |
    | 10 | 🟠 HIGH | **Estado em memória** | Notificações em lista na instância, perdidas a cada restart (sem persistência). |
    | 11 | 🟠 HIGH | **Deleção em cascata manual** | Tasks do usuário deletadas via loop em vez de cascade do SQLAlchemy. |
    | 12 | 🟡 MEDIUM | **Validação duplicada** | Regras de título, status e prioridade repetidas nas routes e em `helpers.py`. |
    | 13 | 🟡 MEDIUM | **Serialização manual verbosa** | `to_dict()` construído campo a campo sem serializer (Marshmallow, Pydantic etc.). |
    | 14 | 🟡 MEDIUM | **Serialização manual verbosa** | Loop de serialização repetido fora do model. |
    | 15 | 🟡 MEDIUM | **Serialização manual verbosa** | Mesmo problema na listagem de tasks por usuário. |
    | 16 | 🟡 MEDIUM | **Bare except** | `except:` sem tipo específico engole erros silenciosamente. |
    | 17 | 🟡 MEDIUM | **Ausência de testes automatizados** | Nenhum arquivo de teste no projeto. |
    | 18 | 🔵 LOW | **Imports não utilizados** | `json, os, sys, time` importados sem uso. |
    | 20 | 🔵 LOW | **Imports não utilizados** | `json` importado sem uso. |
    | 21 | 🔵 LOW | **Imports não utilizados** | `hashlib, json` importados sem uso efetivo. |

## 🚧 *Construção da Skill*

- ### Decisões de design: como estruturou o SKILL.md e os arquivos de referência?

  - **`SKILL.md` enxuto, só com o fluxo:** frontmatter, as 3 fases em ordem (Análise, Auditoria, Refatoração), formatos de saída e princípios. O conhecimento pesado fica em `references/`.
  - **Cinco referências, cada uma ligada a uma fase:**
    - `project-analysis.md`: Fase 1.
    - `anti-patterns-catalog.md` e `report-template.md`: Fase 2.
    - `mvc-guidelines.md`: Fases 2 e 3.
    - `refactoring-playbook.md`: Fase 3.
  - **Leitura sob demanda:** uma tabela no `SKILL.md` indica quando ler cada arquivo, evitando carregar tudo no contexto.
  - **Pausa obrigatória entre as Fases 2 e 3:** nenhum arquivo é alterado sem um "sim" explícito. O único arquivo permitido antes disso é o relatório em `reports/` no diretório raiz.
  - **Descrição "pushy":** lista vários gatilhos ("code smells", "legado", "deprecated", "refatorar") para a skill disparar mesmo sem citar MVC.
  - **Validação exigida:** a Fase 3 grava uma baseline dos endpoints antes de mexer, compara depois e proíbe declarar sucesso sem evidência.

- ### Quais anti-patterns incluiu no catálogo e por quê

  São 12 anti-patterns mais a categoria AP-13 (APIs deprecated), organizados por severidade:

  | Severidade | Anti-patterns | Por quê |
  |---|---|---|
  | CRITICAL | SQL injection, credenciais hardcoded, exposição de dados sensíveis / autenticação fraca | Falhas exploráveis ou risco de perda de dados. Corrigir primeiro. |
  | HIGH | God class, lógica de negócio no controller, estado global, tratamento de erros inadequado | Violam o MVC e impedem manutenção e testes. |
  | MEDIUM | N+1, validação ausente ou duplicada, duplicação (DRY) | Degradam performance e qualidade. |
  | LOW | Magic numbers, nomenclatura inconsistente | Estilo e convenção. |

  Os anti-patterns foram escolhidos porque aparecem nos projetos legados analisados manualmente (credenciais, MD5, lógica no controller, bare except, imports não usados) e porque têm sinais de detecção independentes de stack. O AP-13 é tratado à parte porque o desafio exige detecção de APIs deprecated.

- ### Como garantiu que a skill é agnóstica de tecnologia?

  - **Sinais descritos por padrão, não por sintaxe:** por exemplo, "SQL montado por concatenação, f-string ou template literal, sem placeholders", com exemplos em várias linguagens.
  - **MVC traduzido para a stack detectada:** Model, Controller e Route são adaptados ao idioma do ecossistema, sem impor uma estrutura única.
  - **Tabela de deprecated é só exemplo:** cobre Node, Express, Flask, SQLAlchemy, Django, Java, Spring e PHP, mas a skill manda aplicar o mesmo raciocínio a qualquer API e consultar a documentação oficial (ex.: Context7) em caso de dúvida.
  - **Fase 1 detecta antes de julgar:** identifica linguagem, framework, banco e entry point primeiro. O catálogo não tem receitas presas a um framework.

- ### Desafios encontrados e como resolveu?

  - **Equilíbrio entre genérico e acionável:** sinais por heurística no catálogo e exemplos concretos antes/depois no playbook.
  - **Refatorar sem quebrar contratos:** baseline de endpoints, validação comparativa e lista explícita de mudanças de comportamento intencionais (ex.: parar de expor a senha).
  - **Projetos já organizados:** um princípio evita reestruturar por reestruturar e foca nos desvios reais.
  - **Risco de achados inventados:** a skill exige arquivo e linhas reais e proíbe forçar achados em categorias sem sinal.

## 📈 *Resultados*

- ### Resumo dos relatórios de auditoria dos 3 projetos (quantos findings por severidade em cada?)
  ### 📂 **code-smells-project**
    | Severidade | Qtde |
    |---|---|
    | CRITICAL | 3 |
    | HIGH     | 4 |
    | MEDIUM   | 3 |
    | LOW      | 2 |
    | **Total** | **12** |
  ### 📂 **ecommerce-api-legacy**
    | Severidade | Qtde |
    |---|---|
    | CRITICAL | 2 |
    | HIGH     | 4 |
    | MEDIUM   | 3 |
    | LOW      | 2 |
    | **Total** | **11** |  
  ### 📂 **task-manager-api**

- ### Comparação antes/depois da estrutura de cada projeto.
  ### 📂 **code-smells-project**
  - *Estrutura Anterior*
    ```
    code-smells-project/
    ├── app.py
    ├── controllers.py
    ├── database.py
    ├── models.py
    ├── README.md
    └── requirements.txt
    ```
  - *Estrutura Atual*
    ```
    code-smells-project/
    ├── config/
    │   ├── __init__.py
    │   ├── constants.py            # categorias, status, faixas de desconto
    │   └── settings.py             # SECRET_KEY, DEBUG, HOST, PORT, DB_PATH, ADMIN_TOKEN...
    ├── controllers/
    │   ├── __init__.py
    │   ├── pedido_controller.py
    │   ├── produto_controller.py
    │   ├── relatorio_controller.py
    │   ├── sistema_controller.py
    │   └── usuario_controller.py
    ├── database/
    │   ├── __init__.py
    │   ├── connection.py           # conexão por request (flask.g)
    │   └── schema.py               # criação de tabelas + seed
    ├── middlewares/
    │   ├── __init__.py
    │   ├── auth.py                 # admin_required (X-Admin-Token)
    │   └── error_handler.py        # tratamento central de erros
    ├── models/
    │   ├── __init__.py
    │   ├── pedido_model.py
    │   ├── produto_model.py
    │   ├── relatorio_model.py
    │   ├── sistema_model.py
    │   └── usuario_model.py
    ├── routes/
    │   └── __init__.py             # blueprints: produtos, usuarios, pedidos, relatorios, sistema
    ├── services/
    │   ├── __init__.py
    │   ├── notificacao_service.py
    │   ├── pedido_service.py
    │   ├── relatorio_service.py
    │   └── usuario_service.py
    ├── validators/
    │   ├── __init__.py
    │   ├── pedido_validator.py
    │   ├── produto_validator.py
    │   └── usuario_validator.py
    ├── views/
    │   ├── __init__.py
    │   └── serializers.py          # serializa sem expor senha
    ├── .env.example
    ├── app.py                      # composition root (create_app)
    ├── exceptions.py               # AppError, ValidationError, NotFoundError...
    ├── loja.db                     # ignorado pelo git
    ├── README.md
    └── requirements.txt
    ```
  ### 📂 **ecommerce-api-legacy**
  - *Estrutura Anterior*
    ```
    ecommerce-api-legacy/
    ├── src/
    │   ├── app.js
    │   ├── AppManager.js
    │   └── utils.js
    ├── api.http
    ├── package-lock.json
    ├── package.json
    └── README.md
    ```
  - *Estrutura Atual*
    ~~~
    ecommerce-api-legacy/
    ├── src/
    │   ├── app.js                    # composition root
    │   ├── constants.js
    │   ├── config/
    │   │   └── index.js
    │   ├── controllers/
    │   │   ├── checkoutController.js
    │   │   ├── reportController.js
    │   │   └── userController.js
    │   ├── database/
    │   │   ├── connection.js
    │   │   └── schema.js
    │   ├── middlewares/
    │   │   ├── adminAuth.js
    │   │   └── errorHandler.js
    │   ├── models/
    │   │   ├── auditLogModel.js
    │   │   ├── courseModel.js
    │   │   ├── enrollmentModel.js
    │   │   ├── paymentModel.js
    │   │   ├── reportModel.js
    │   │   └── userModel.js
    │   ├── routes/
    │   │   └── index.js
    │   ├── services/
    │   │   ├── checkoutService.js
    │   │   ├── paymentGateway.js
    │   │   └── reportService.js
    │   ├── utils/
    │   │   ├── asyncHandler.js
    │   │   ├── errors.js
    │   │   └── password.js
    │   └── validators/
    │       └── requestValidator.js
    ├── .env.example
    ├── api.http
    ├── package.json
    ├── package-lock.json
    └── README.md
    ~~~
  ### 📂 **task-manager-api**
  - *Estrutura Anterior*
    ```
    task-manager-api/
    ├── models/
    │   ├── __init__.py
    │   ├── category.py
    │   ├── task.py
    │   └── user.py
    ├── routes/
    │   ├── __init__.py
    │   ├── report_routes.py
    │   ├── task_routes.py
    │   └── user_routes.py
    ├── services/
    │   ├── __init__.py
    │   └── notification_service.py
    ├── utils/
    │   ├── __init__.py
    │   └── helpers.py
    ├── app.py
    ├── database.py
    ├── README.md
    ├── requirements.txt
    └── seed.py
    ```
  - *Estrutura Atual*

- ### Checklist de validação preenchido para cada projeto.
  ### 📂 **code-smells-project**
  ```markdown
  ## Checklist de Validação

  ### Fase 1 - Análise
  - ✅ Linguagem detectada corretamente
  - ✅ Framework detectado corretamente
  - ✅ Domínio da aplicação descrito corretamente
  - ✅ Número de arquivos analisados condiz com a realidade

  ### Fase 2 - Auditoria
  - ✅ Relatório segue o template definido nos arquivos de referência
  - ✅ Cada finding tem arquivo e linhas exatos
  - ✅ Findings ordenados por severidade (CRITICAL → LOW)
  - ✅ Mínimo de 5 findings identificados
  - ✅ Detecção de APIs deprecated incluída (se aplicável)
  - ✅ Skill pausa e pede confirmação antes da Fase 3

  ### Fase 3 - Refatoração
  - ✅ Estrutura de diretórios segue padrão MVC
  - ✅ Configuração extraída para módulo de config (sem hardcoded)
  - ✅ Models criados para abstrair dados
  - ✅ Views/Routes separadas para visualização ou roteamento
  - ✅ Controllers concentram o fluxo da aplicação
  - ✅ Error handling centralizado
  - ✅ Entry point claro
  - ✅ Aplicação inicia sem erros
  - ✅ Endpoints originais respondem corretamente
  ```
  ### 📂 **ecommerce-api-legacy**
  ```markdown
  ## Checklist de Validação

  ### Fase 1 - Análise
  - ✅ Linguagem detectada corretamente
  - ✅ Framework detectado corretamente
  - ✅ Domínio da aplicação descrito corretamente
  - ✅ Número de arquivos analisados condiz com a realidade

  ### Fase 2 - Auditoria
  - ✅ Relatório segue o template definido nos arquivos de referência
  - ✅ Cada finding tem arquivo e linhas exatos
  - ✅ Findings ordenados por severidade (CRITICAL → LOW)
  - ✅ Mínimo de 5 findings identificados
  - ✅ Detecção de APIs deprecated incluída (se aplicável)
  - ✅ Skill pausa e pede confirmação antes da Fase 3

  ### Fase 3 - Refatoração
  - ✅ Estrutura de diretórios segue padrão MVC
  - ✅ Configuração extraída para módulo de config (sem hardcoded)
  - ✅ Models criados para abstrair dados
  - ✅ Views/Routes separadas para visualização ou roteamento
  - ✅ Controllers concentram o fluxo da aplicação
  - ✅ Error handling centralizado
  - ✅ Entry point claro
  - ✅ Aplicação inicia sem erros
  - ✅ Endpoints originais respondem corretamente
  ```
  ### 📂 **task-manager-api**
  ```markdown
  ## Checklist de Validação

  ### Fase 1 - Análise
  - ✅ Linguagem detectada corretamente
  - ✅ Framework detectado corretamente
  - ✅ Domínio da aplicação descrito corretamente
  - ✅ Número de arquivos analisados condiz com a realidade

  ### Fase 2 - Auditoria
  - ✅ Relatório segue o template definido nos arquivos de referência
  - ✅ Cada finding tem arquivo e linhas exatos
  - ✅ Findings ordenados por severidade (CRITICAL → LOW)
  - ✅ Mínimo de 5 findings identificados
  - ✅ Detecção de APIs deprecated incluída (se aplicável)
  - ✅ Skill pausa e pede confirmação antes da Fase 3

  ### Fase 3 - Refatoração
  - ✅ Estrutura de diretórios segue padrão MVC
  - ✅ Configuração extraída para módulo de config (sem hardcoded)
  - ✅ Models criados para abstrair dados
  - ✅ Views/Routes separadas para visualização ou roteamento
  - ✅ Controllers concentram o fluxo da aplicação
  - ✅ Error handling centralizado
  - ✅ Entry point claro
  - ✅ Aplicação inicia sem erros
  - ✅ Endpoints originais respondem corretamente
  ```

- ### Screenshots ou logs mostrando as aplicações rodando após refatoração.

  ### 📂 **code-smells-project**
  ![Evidência 1_1](screenshots\code-smells-1.png)
  ![Evidência 1_2](screenshots\code-smells-2.png)
  ![Evidência 1_3](screenshots\code-smells-3.png)
  ![Evidência 1_4](screenshots\code-smells-4.png)
  ### 📂 **ecommerce-api-legacy**
  ![Evidência 2_0](screenshots\ecommerce-api-legacy-0.png)
  ![Evidência 2_1](screenshots\ecommerce-api-legacy-1.png)
  ![Evidência 2_2](screenshots\ecommerce-api-legacy-2.png)
  ![Evidência 2_3](screenshots\ecommerce-api-legacy-3.png)
  ![Evidência 2_4](screenshots\ecommerce-api-legacy-4.png)
  ![Evidência 2_5](screenshots\ecommerce-api-legacy-5.png)
  ### 📂 **task-manager-api**

- ### Observações sobre como a skill se comportou em stacks diferentes.

## ⏯️ *Como Executar*
### Pré-requisitos:
  - Claude Code instalado.
  - Python e o pip install -r requirements.txt do projeto, ou Node e npm install, conforme o projeto.
  - Skill presente em `<projeto>/.claude/skills/refactor-arch/`.
  - Context7 MCP opcional, para checar APIs deprecated.
### Comandos:
  ```bash
  # Executar a skill no projeto 1
  cd code-smells-project
  claude "/refactor-arch"
  ```
  ```bash
  # Executar a skill no projeto 2
  cd ecommerce-api-legacy
  claude "/refactor-arch"
  ```
  ```bash
  # Executar a skill no projeto 3
  cd task-manager-api
  claude "/refactor-arch"
  ```
  Observação: Responder quando a Fase 2 perguntar.

### Como validar:
  - A aplicação sobe sem erros.
  - Os endpoints respondem com o mesmo status e formato do baseline, com pelo menos um caminho de sucesso e um de erro por recurso.
  - O resumo da Fase 3 mostra [OK] nos itens de validação.
  - Os achados tratados não aparecem mais ao reler o catálogo.
  - O relatório existe em reports/audit-project-<N>.md.