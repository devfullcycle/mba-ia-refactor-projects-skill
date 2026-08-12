# Antipattern Catalog

## Objetivo
Catalogar anti-patterns, vulnerabilidades e sinais de APIs deprecated com severidade, para uso na Fase 2 de auditoria.

### CRITICAL
- **God Class / God Module**
  - Sinais: arquivo único contém rotas, lógica de negócio, acesso a dados e validação.
  - Impacto: impossível testar isoladamente, altíssimo acoplamento.

- **Hardcoded Secrets**
  - Sinais: `SECRET_KEY`, senhas, chaves API, credenciais ou informações sensíveis em código.
  - Impacto: vazamento de segredos, ambiente inseguro.

- **SQL Injection / Concatenation SQL**
  - Sinais: queries construídas com concatenação de strings, interpolação direta de inputs.
  - Impacto: execução de SQL arbitrário.

- **Backdoor / Unsafe Admin Query**
  - Sinais: endpoints que executam SQL arbitrário ou resetam DB sem autenticação.
  - Impacto: falha de segurança grave.

### HIGH
- **Business Logic in Controller/Route**
  - Sinais: cálculos, regras de domínio e validações pesadas dentro de rotas ou controllers.
  - Impacto: dificulta testes e manutenção.

- **Global Mutable State**
  - Sinais: caches globais, variáveis de configuração mutáveis ou singletons mal definidos.
  - Impacto: comportamento imprevisível em runtime.

- **Deprecated / Vulnerable API Usage**
  - Sinais: uso de métodos antigos, `badCrypto`, `fs.existsSync` sem tratamento, `require.extensions`, ou APIs sem suporte.
  - Impacto: risco de quebra futura e segurança reduzida.

### MEDIUM
- **N+1 Query**
  - Sinais: loops que fazem consultas por item, `for`/`foreach` que executam consultas SQL ou ORM repetidas.
  - Impacto: degradação de performance.

- **Mixed Responsibilities**
  - Sinais: rotas que também atualizam modelos, manipulam respostas e fazem persistência direta.
  - Impacto: acoplamento e duplicação.

- **Lack of Validation / Missing Input Checks**
  - Sinais: parâmetros usados sem validação adequada.
  - Impacto: erros, comportamento inesperado e possíveis vulnerabilidades.

### LOW
- **Magic Values / Poor Naming**
  - Sinais: strings não documentadas, variáveis sem significado, números mágicos.
  - Impacto: legibilidade reduzida.

- **Duplicate Code**
  - Sinais: blocos repetidos de validação ou mapeamento.
  - Impacto: manutenção dificultada.

- **Implicit Configuration**
  - Sinais: configurações definidas diretamente no código (porta, URI, debug).
  - Impacto: dificuldade de mudar ambiente.

## Deprecated API Examples
- Node.js `badCrypto` custom hashing → use `bcrypt` ou `crypto.pbkdf2`.
- Express: `app.use(bodyParser.json())` / `body-parser` → use `express.json()`.
- Flask: `app.config['DEBUG'] = True` em produção / `Flask` debug no código → use ambiente e `FLASK_ENV`.
- SQLite string concatenation → use query parametrizada ou ORM.

## Como usar
- Compare padrões do código com os sinais acima.
- Para cada finding, inclua severidade e recomendação de correção.
- Se não houver sinal exato, use julgamento conservador baseado em acoplamento e risco.
