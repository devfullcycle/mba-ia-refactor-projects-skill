# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http`.

---

## Análise Manual

### CRITICAL

#### 1. Hardcoded Credentials
- **Arquivo:** `src/utils.js:2-5`
- **Problema:** Senha do banco (`"senha_super_secreta_prod_123"`), chave do gateway de pagamento (`"pk_live_1234567890abcdef"`), credenciais SMTP — tudo hardcoded no código-fonte.
- **Impacto:** Qualquer pessoa com acesso ao repo tem credenciais de produção. Vazamento no Git expõe todos os sistemas integrados.
- **Severidade:** CRITICAL

#### 2. Weak Cryptography
- **Arquivo:** `src/utils.js:17-23`
- **Problema:** Função `badCrypto()` faz um loop de 10.000 iterações concatenando os 2 primeiros chars de base64, depois trunca para 10 chars. Não é hash, não tem salt, é trivialmente reversível.
- **Impacto:** Senhas dos usuários não estão protegidas. Qualquer database leak expõe todas as senhas.
- **Severidade:** CRITICAL

#### 3. Credit Card Logging
- **Arquivo:** `src/AppManager.js:45`
- **Problema:** `console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`)` — loga o número completo do cartão de crédito e a chave do gateway no console.
- **Impacto:** Violação de PCI-DSS. Números de cartão ficam em logs accessíveis a qualquer operador do sistema.
- **Severidade:** CRITICAL

### HIGH

#### 4. God Class (AppManager)
- **Arquivo:** `src/AppManager.js:1-141`
- **Problema:** Classe única responsável por: inicializar o banco, criar tabelas, popular seeds, definir todas as rotas, processar pagamentos, gerenciar matrículas, gerar relatórios, deletar usuários. 141 linhas fazendo tudo.
- **Impacto:** Impossível testar qualquer funcionalidade isoladamente. Qualquer mudança afeta o sistema inteiro.
- **Severidade:** HIGH

#### 5. Business Logic in Route Handler
- **Arquivo:** `src/AppManager.js:28-78`
- **Problema:** O handler do `/api/checkout` faz tudo: valida input, busca curso, busca/cria usuário, processa pagamento (com lógica de cartão), cria matrícula, cria pagamento, cria audit log, faz cache. Tudo em um único handler.
- **Impacto:** Impossível reutilizar lógica de pagamento, matrícula ou criação de usuário em outro contexto. Impossível testar unitariamente.
- **Severidade:** HIGH

#### 6. Callback Hell
- **Arquivo:** `src/AppManager.js:37-77`
- **Problema:** 4-5 níveis de callbacks aninhadas: `db.get()` → `db.get()` → `db.run()` → `db.run()` → `db.run()`. Usa `let self = this` para contornar escopo.
- **Impacto:** Código difícil de ler e manter. Erros em callbacks internas são difíceis de rastrear. Impossível usar try/catch para error handling.
- **Severidade:** HIGH

#### 7. No Cascade Delete
- **Arquivo:** `src/AppManager.js:131-137`
- **Problema:** DELETE de usuário remove da tabela `users` mas não limpa `enrollments` nem `payments`. A própria resposta diz: `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."`
- **Impacto:** Dados órfãos no banco. Relatórios financeiros quebram (referenciam usuários inexistentes).
- **Severidade:** HIGH

### MEDIUM

#### 8. N+1 Query Problem
- **Arquivo:** `src/AppManager.js:83-128`
- **Problema:** O financial-report faz: para cada curso → query matrículas; para cada matrícula → query user; para cada matrícula → query payment. Com 10 cursos de 50 matrículas cada = 500+ queries ao invés de 1 JOIN.
- **Impacto:** Relatório financeiro fica cada vez mais lento conforme o sistema cresce.
- **Severidade:** MEDIUM

#### 9. Global Mutable State
- **Arquivo:** `src/utils.js:9-10`
- **Problema:** `let globalCache = {}` e `let totalRevenue = 0` — variáveis globais mutáveis exportadas como módulo. `totalRevenue` nunca é atualizado, `globalCache` é preenchido mas nunca lido de forma útil.
- **Impacto:** Estado compartilhado entre requests pode causar race conditions e comportamento imprevisível sob concorrência.
- **Severidade:** MEDIUM

#### 10. In-Memory Database
- **Arquivo:** `src/AppManager.js:8`
- **Problema:** `this.db = new sqlite3.Database(':memory:')` — todos os dados são perdidos quando o servidor reinicia.
- **Impacto:** Impossível usar em produção. Dados de matrículas, pagamentos e usuários desaparecem a cada restart.
- **Severidade:** MEDIUM

### LOW

#### 11. Poor Variable Naming
- **Arquivo:** `src/AppManager.js:29-33`
- **Problema:** Variáveis com nomes obscuros: `u` (usuário), `e` (email), `p` (password), `cid` (course_id), `cc` (cartão de crédito). No financial-report: `enrPending`, `coursesPending` como contadores de callback.
- **Impacto:** Código difícil de entender. Novos desenvolvedores precisam decifrar o que cada variável representa.
- **Severidade:** LOW

#### 12. sqlite3 Verbose Mode
- **Arquivo:** `src/AppManager.js:1`
- **Problema:** `require('sqlite3').verbose()` habilita tracing detalhado do SQLite, gerando logs excessivos em produção.
- **Impacto:** Polui logs com informações internas do driver SQLite.
- **Severidade:** LOW

#### 13. Generic Error Responses
- **Arquivo:** `src/AppManager.js:passim`
- **Problema:** Erros retornam strings genéricas como `"Erro DB"`, `"Erro Matrícula"`, `"Erro Pagamento"`. Sem códigos de erro estruturados, sem logs do erro real para o cliente.
- **Impacto:** Difícil debugar problemas. Clientes da API não têm informação útil para reportar.
- **Severidade:** LOW
