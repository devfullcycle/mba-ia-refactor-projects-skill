# Catálogo de Anti-Patterns e Code Smells

Este catálogo orienta a **Fase 2 (Auditoria Arquitetural)** da skill `refactor-arch`. Cada achado deve ser classificado de acordo com o impacto arquitetural, segurança, manutenibilidade e confiabilidade da aplicação.

---

## Tabela de Classificação de Severidade

| Severidade | Critério de Impacto | Exemplos Típicos |
|---|---|---|
| **CRITICAL** | Falhas graves de segurança ou integridade estrutural que permitem comprometimento total do sistema, perda/vazamento de dados, execução remota de código ou violação total da separação de camadas. | SQL Injection via concatenação/interpolação de strings; Rota administrativa de query arbitrária aberta; God Class/God Method que monopoliza banco, roteamento e lógica de múltiplos domínios; Credenciais ou chaves privadas críticas hardcoded (banco prod, gateway de pagamento). |
| **HIGH** | Fortes violações dos padrões de camadas (MVC) e princípios SOLID, expondo dados sensíveis ou gerando forte acoplamento que inviabiliza testes automatizados e evolução segura. | Queries e transações de banco executadas diretamente dentro de Controllers/Rotas; Segredos de sessão ou SMTP expostos no código; Exposição de senhas/hashes em DTOs/respostas JSON; Criptografia defasada/quebrada (MD5 sem salt, algoritmos caseiros); Exclusão de registros sem integridade referencial/cascade; Estado global mutável compartilhado entre requisições. |
| **MEDIUM** | Problemas de complexidade algorítmica, gargalos de performance moderados, ofuscação de falhas e violação da coesão de métodos. | Problema de Queries N+1 (queries dentro de loops ou queries aninhadas recursivamente); Complexidade ciclomática elevada (pirâmides de `if/else`); Tratamento silencioso de exceções (`except: pass`, `catch(e) {}` engolindo o erro); Regras de validação de negócio dispersas nos controllers; Inconsistência de respostas de erro; Ausência de desvinculação prévia de dependentes em relacionamentos opcionais (deleção destrutiva acidental). |
| **LOW** | Desvios de padronização, manutenibilidade, legibilidade, dead code e uso de padrões defasados. | Endpoints sem especificação explícita do verbo HTTP; Falta de validação estrita de dados de entrada/saída; Imports não utilizados; Variáveis mágicas ("magic numbers"); Nomenclatura críptica ou abreviada; Uso de APIs obsoletas/deprecated sem quebra imediata. |

---

## Catálogo Detalhado de Anti-Patterns

### 1. [CRITICAL] SQL Injection & Arbitrary Query Execution
- **ID**: `SEC-001`
- **Sinais de Detecção**:
  - Concatenação direta de variáveis em strings SQL: `cursor.execute("SELECT ... WHERE id = " + str(id))` ou `"INSERT INTO ... VALUES ('" + nome + "')"` ou `f"SELECT ... WHERE id = {id}"`.
  - Falta de tuplas/listas de parâmetros nos drivers (`cursor.execute(sql, (param,))` ou `db.get(sql, [param])`).
  - Endpoints que recebem raw SQL do payload JSON e o executam diretamente no banco de dados (ex.: rota `/admin/query`).
- **Impacto**: Risco catastrófico de vazamento completo, alteração ou exclusão de todos os dados do banco por invasores.
- **Remediação**: Usar exclusivamente queries parametrizadas (prepared statements) com placeholders (`?` ou `%s`) ou abstração ORM. Remover completamente endpoints de execução de SQL arbitrário ou restringir a ferramentas de migração offline.

---

### 2. [CRITICAL] Exposed Hardcoded Sensitive Credentials
- **ID**: `SEC-002`
- **Sinais de Detecção**:
  - Chaves de API de produção, senhas de banco ou segredos de gateway declarados no código-fonte (ex.: `dbPass = "senha_super_secreta_prod_123"`, `paymentGatewayKey = "pk_live_1234567890abcdef"`).
  - Logs que imprimem números de cartão de crédito, senhas ou tokens completos em console/arquivos (ex.: `console.log("Processando cartão " + cc)`).
- **Impacto**: Comprometimento direto da infraestrutura de produção, violação de normas como PCI-DSS e LGPD/GDPR, risco de fraudes financeiras.
- **Remediação**: Extrair todas as credenciais sensíveis para variáveis de ambiente (`os.getenv`, `process.env`) carregadas via módulo de configuração (`config/settings`). Mascarar dados de pagamento e dados sensíveis antes de qualquer logging.

---

### 3. [CRITICAL] Monolithic God Class / God File
- **ID**: `ARCH-001`
- **Sinais de Detecção**:
  - Arquivo único ou classe contendo centenas de linhas gerenciando simultaneamente schemas de banco, conexões, queries, lógicas de domínio múltiplas (produtos, usuários, pedidos, relatórios), rotas HTTP e serialização (ex.: `models.py` contendo tudo ou `AppManager.js` "Frankenstein").
  - Múltiplas responsabilidades concorrentes violando o Single Responsibility Principle (SRP).
- **Impacto**: Impossível isolar regras de negócio, testar em unidade, auditar ou efetuar manutenção sem causar regressões colaterais em toda a aplicação.
- **Remediação**: Decompor o monólito em camadas MVC distintas (`models/`, `views/routes/`, `controllers/`, `config/`), segregando cada entidade em seu próprio módulo.

---

### 4. [HIGH] Direct Database Operations in Controllers/Routes
- **ID**: `ARCH-002`
- **Sinais de Detecção**:
  - Chamadas diretas a cursores de banco de dados (`get_db()`, `cursor.execute()`, `db.run()`, `this.db.get()`, `Task.query`) implementadas dentro de funções de rota ou manipuladores de requisição HTTP (ex.: `health_check()` executando `cursor.execute()`, ou rotas Express fazendo queries inline com callbacks).
- **Impacto**: Acoplamento extremo entre a camada de transporte (HTTP) e a camada de persistência; torna os controladores pesados e impossibilita a reutilização de regras em outros contextos (CLI, fila, testes).
- **Remediação**: Mover todas as operações de banco para Models/Repositories específicos. O Controller deve apenas orquestrar a requisição, chamar o Model/Service e devolver a resposta HTTP.

---

### 5. [HIGH] Broken Cryptography & Plaintext Password Exposure
- **ID**: `SEC-003`
- **Sinais de Detecção**:
  - Hashing de senhas com algoritmos criptograficamente inseguros ou obsoletos (ex.: `hashlib.md5(pwd.encode()).hexdigest()` sem salt).
  - Algoritmos caseiros de criptografia (ex.: função `badCrypto()` que faz loop com base64 e substring).
  - Métodos de serialização de entidades (ex.: `to_dict()`) que incluem o campo `'password'` no payload retornado para a API pública.
  - Senhas armazenadas em texto puro no banco.
- **Impacto**: Vazamento de credenciais de usuários em requisições de consulta ou quebra trivial de hashes em vazamentos de dados por ataques de rainbow table.
- **Remediação**: Utilizar algoritmos modernos e com salt (como `bcrypt`, `pbkdf2` ou `argon2`). Nunca incluir o campo de senha no retorno do método `to_dict()` ou de serialização de usuário.

---

### 6. [HIGH] Unsafe Deletion & Broken Referential Integrity
- **ID**: `DATA-001`
- **Sinais de Detecção**:
  - Execução de `DELETE` na tabela pai sem verificação prévia, exclusão em cascata ou transação (ex.: `DELETE FROM users WHERE id = ?` deixando registros órfãos nas tabelas `enrollments`, `payments`, ou `tasks`).
- **Impacto**: Corrupção da consistência relacional do banco de dados, relatórios financeiros inconsistentes e erros `NullPointer` / `KeyError` em leituras subsequentes.
- **Remediação**: Implementar foreign keys com `ON DELETE CASCADE` ou tratar a exclusão dentro de uma transação no Model/Service que limpe ou desative (soft delete) as entidades associadas.

---

### 7. [HIGH] Uncontrolled Mutable Global State
- **ID**: `ARCH-003`
- **Sinais de Detecção**:
  - Declaração de variáveis globais mutáveis no escopo de módulos (ex.: `globalCache = {}`, `totalRevenue = 0`, `db_connection = None` com `global db_connection`).
- **Impacto**: Condições de corrida (race conditions) em ambientes multi-thread/multi-processo, vazamento de memória e efeitos colaterais imprevisíveis entre requisições concorrentes.
- **Remediação**: Encapsular o estado dentro de instâncias de serviço com injeção de dependência ou adotar ferramentas dedicadas de cache/sessão (Redis, cache thread-local).

---

### 8. [MEDIUM] Destructive Cascade Deletion on Optional Relationships & Missing Prior Disassociation
- **ID**: `DATA-002`
- **Sinais de Detecção**:
  - Exclusão de entidades secundárias ou organizacionais (ex.: categorias, tags, departamentos) configuradas com deleção em cascata (`cascade="all, delete-orphan"` ou `ON DELETE CASCADE`) que destroem entidades principais de negócio (como tarefas ou produtos), quando o relacionamento é opcional (`nullable=True`).
  - Falta de validação prévia e desvinculação (`SET NULL`) de registros filhos antes de excluir a entidade pai opcional.
- **Impacto**: Perda de dados e histórico de entidades dependentes por efeito colateral imprevisto na exclusão de uma entidade meramente classificatória.
- **Remediação**: Adicionar verificação prévia no Controller/Model para validar e desvincular registros dependentes (ex.: atribuir `None` / `NULL` à chave estrangeira) antes de remover a entidade principal opcional, configurando a foreign key com `ON DELETE SET NULL` e removendo `cascade='all, delete-orphan'` de relacionamentos opcionais no ORM.

---

### 9. [MEDIUM] N+1 Query Problem & Nested Queries in Loops
- **ID**: `PERF-001`
- **Sinais de Detecção**:
  - Executar uma query SQL de busca em lote e, para cada item iterado, disparar uma ou mais novas queries adicionais no banco (ex.: buscar todos os pedidos e para cada pedido fazer `SELECT * FROM itens_pedido`, e para cada item fazer `SELECT nome FROM produtos`; ou em Express, cascata de callbacks aninhando `SELECT courses` -> `SELECT enrollments` -> `SELECT users` -> `SELECT payments`).
- **Impacto**: Degradação exponencial de desempenho (explosão no número de conexões e queries ao banco) conforme a base de dados cresce.
- **Remediação**: Reescrever consultas usando `JOIN` (ex.: `LEFT JOIN itens_pedido ... JOIN produtos`), ou fazer queries em lote com operador `IN (...)` ou `eager loading` no ORM (`joinedload` / `selectinload`).

---

### 10. [MEDIUM] Heavy Health Check & Unnecessary Table Counts
- **ID**: `PERF-002`
- **Sinais de Detecção**:
  - Endpoint de health check (`/health` ou sondas de liveness/readiness) executando consultas pesadas de negócio, como `COUNT(*)` em múltiplas tabelas (`produtos`, `usuarios`, `pedidos`), scans completos ou agregações analíticas a cada requisição de probe.
- **Impacto**: Sondas de infraestrutura (Kubernetes, AWS ALB, monitoramento) disparam a cada poucos segundos. Executar contagens totais gera sobrecarga severa de I/O, bloqueios de leitura e risco de *cascading failure* ou timeout sob alta carga.
- **Remediação**: Limitar a checagem a uma verificação atômica de conectividade (ex.: `SELECT 1;` ou ping do driver/pool), retornando HTTP 200 se saudável ou 503 se degradado. Métricas de contagem devem pertencer a rotas dedicadas de telemetria/dashboard (`/metrics` ou `/admin/stats`).

---

### 11. [MEDIUM] High Cyclomatic Complexity & Deeply Nested Conditionals
- **ID**: `CODE-001`
- **Sinais de Detecção**:
  - Métodos com 4 ou mais níveis de indentação de `if/else` aninhados (ex.: checagem de `due_date`, seguida de checagem de data limite, seguida de checagem de status, com múltiplos ramos `else`).
  - Funções longas que combinam validações de múltiplos campos, regras de negócio e formatação de resposta.
- **Impacto**: Código de difícil leitura, propenso a erros lógicos durante manutenções e com caminhos de execução não cobertos por testes.
- **Remediação**: Aplicar Guard Clauses (retorno antecipado), decompor funções em métodos auxiliares coesos e utilizar mapeamentos/dicionários de lookup.

---

### 12. [MEDIUM] Swallowed Exceptions & Silent Failures
- **ID**: `CODE-002`
- **Sinais de Detecção**:
  - Blocos `try: ... except:` sem especificação de tipo de exceção e sem registrar traceback (ex.: `except: return jsonify({'error': 'Erro interno'}), 500`).
  - Blocos de erro que suprimem a falha sem logging estruturado ou apenas retornam mensagens genéricas sem persistir diagnóstico.
- **Impacto**: Impossibilidade de realizar troubleshooting e debugar incidentes em produção, mascarando bugs graves do sistema.
- **Remediação**: Capturar exceções específicas, registrar o erro com traceback via módulo padrão de logging (`logging.error(...)`), e centralizar o tratamento de erros em middlewares/handlers dedicados.

---

### 13. [LOW] Deprecated APIs & Obsolete Constructs
- **ID**: `DEP-001`
- **Sinais de Detecção**:
  - Uso de métodos marcados como obsoletos nas versões modernas das linguagens e bibliotecas:
    - Em Python: `datetime.utcnow()` (deprecated desde Python 3.12, gera warnings de timezone naive).
    - Em Express: uso de padrões legados de tratamento de rotas sem promessas assíncronas nativas (`async/await`) ou sem `next(err)`.
- **Impacto**: Warnings no log, risco de quebra em atualizações de versão de runtime e inconsistências em cálculos de fuso horário.
- **Remediação**: Substituir `datetime.utcnow()` por `datetime.now(timezone.utc)`. Adotar sintaxe moderna e assíncrona (`async/await`) com tratamento padronizado.

---

### 14. [LOW] Missing Explicit HTTP Methods & Inconsistent Routing
- **ID**: `ARCH-004`
- **Sinais de Detecção**:
  - Rotas declaradas sem a lista explícita de métodos HTTP suportados (ex.: `@app.route("/")` ou `@app.route("/health")` sem `methods=["GET"]`).
- **Impacto**: Ambiguidade na definição de contratos da API, permitindo que a rota aceite comportamentos não previstos ou dependa de defaults implícitos do framework.
- **Remediação**: Especificar sempre `methods=["GET"]`, `methods=["POST"]`, etc. de forma explícita em todas as anotações de rota.

---

### 15. [LOW] Dead Code & Unused Imports
- **ID**: `CODE-003`
- **Sinais de Detecção**:
  - Declaração de imports no topo do arquivo que nunca são chamados no restante do módulo (ex.: `import os, sys, json, datetime` onde apenas `datetime` é utilizado).
- **Impacto**: Poluição do namespace, tempo de inicialização marginalmente maior e distração cognitiva para desenvolvedores.
- **Remediação**: Remover todos os imports não referenciados e manter o código enxuto.

---

### 16. [LOW] Magic Numbers & Unsanitized Inputs
- **ID**: `CODE-004`
- **Sinais de Detecção**:
  - Literais numéricos e de strings espalhados no código sem constantes nomeadas (ex.: `200`, `5`, `10000`, `'informatica'`).
  - Validações ad-hoc repetidas em múltiplos arquivos em vez de um validador reutilizável.
- **Impacto**: Dificuldade para alterar regras de negócio centralizadas e inconsistência entre endpoints.
- **Remediação**: Definir constantes de domínio ou Enums (ex.: `PRIORITY_MIN = 1`, `PRIORITY_MAX = 5`).
