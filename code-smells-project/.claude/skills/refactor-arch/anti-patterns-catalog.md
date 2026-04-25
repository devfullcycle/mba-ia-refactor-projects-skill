# Anti-Patterns Catalog

Cada anti-pattern contem nome, severidade, sinais de deteccao e descricao conceitual.

---

## CRITICAL

### 1. SQL Injection

**Conceito:** Queries SQL construidas com string concatenation ou interpolacao usando input do usuario.

**Sinais de deteccao:**
- Concatenacao de variaveis dentro de strings SQL
- Interpolacao de strings (f-strings, template literals) em queries
- Query building dinamico com input do usuario sem uso de parametros preparados
- Qualquer lugar onde input externo e injetado diretamente em uma string SQL

**Impacto:** Permite que atacantes executem SQL arbitrario no banco — leitura, modificacao ou destruicao de dados.

---

### 2. Hardcoded Credentials / Secrets

**Conceito:** Senhas, chaves de API, tokens ou credenciais escritas diretamente no codigo-fonte.

**Sinais de deteccao:**
- Variaveis de config recebendo strings literais que parecem credenciais
- Strings de conexao de banco com senha embutida
- Chaves de gateway de pagamento, SMTP, ou servicos externos no codigo
- SECRET_KEY, API_KEY, PASSWORD ou similares atribuidos a valores fixos
- Senhas de usuarios seed/fixture escritas em plaintext

**Impacto:** Qualquer pessoa com acesso ao codigo tem acesso a todos os sistemas integrados. Vazamento no repositorio expoe credenciais de producao.

---

### 3. God Class / God File

**Conceito:** Um unico arquivo ou classe que acumula multiplas responsabilidades e dominios.

**Sinais de deteccao:**
- Arquivo com mais de 200 linhas tratando 3 ou mais entidades/domínios diferentes
- Uma classe que inicializa banco, define rotas, contem logica de negocio e acessa dados
- Funcoes para entidades distintas (ex: usuarios, produtos, pedidos) no mesmo arquivo
- Impossibilidade de testar uma funcionalidade sem carregar tudo

**Impacto:** Impossivel testar em isolamento. Mudancas em um dominio podem quebrar outro. Viola o Single Responsibility Principle.

---

### 4. Unauthenticated Sensitive Endpoints

**Conceito:** Endpoints que executam operacoes privilegiadas sem verificar a identidade do usuario.

**Sinais de deteccao:**
- Rotas administrativas (reset de banco, execucao de queries) sem middleware de autenticacao
- Endpoints que aceitam e executam comandos arbitrarios (SQL, shell) do corpo da requisicao
- Operacoes destrutivas (DELETE, DROP, reset) sem verificacao de autorizacao

**Impacto:** Qualquer usuario anonimo pode executar operacoes administrativas, destruir dados ou acessar informacoes sensíveis.

---

### 5. Weak Cryptography

**Conceito:** Uso de algoritmos criptograficos inseguros ou implementacoes caseiras para proteger dados sensíveis.

**Sinais de deteccao:**
- Hashing de senhas com algoritmos quebrados (MD5, SHA1)
- Funcoes de criptografia customizadas (loops de encoding, XOR caseiro)
- Senhas armazenadas em plaintext
- Hashes sem salt
- Qualquer funcao que nao use uma biblioteca criptografica reconhecida para senhas

**Impacto:** Senhas e dados sensíveis podem ser recuperados facilmente. Database leak expoe todos os usuarios.

---

## HIGH

### 6. Business Logic in Route/View Layer

**Conceito:** Logica de negocio (calculos, regras, notificacoes) embutida nos handlers de rotas ao inves de estar em controllers ou services separados.

**Sinais de deteccao:**
- Route handlers executando queries de banco diretamente
- Calculos de preco, desconto ou transicoes de estado dentro de funcoes de rota
- Logica de notificacao (email, SMS, push) embutida em rotas
- Validacao complexa de regras de negocio misturada com parseamento de request
- Simulacao de servicos externos via print/log dentro de rotas

**Impacto:** Impossivel reutilizar logica em outro contexto (CLI, tests, outros endpoints). Impossivel testar unitariamente.

---

### 7. Sensitive Data Exposure in API Responses

**Conceito:** Endpoints retornando dados sensíveis (senhas, hashes, secrets, cartoes) nas respostas HTTP.

**Sinais de deteccao:**
- Metodos de serializacao de modelos incluindo campos de senha ou hash
- Respostas de API retornando campos como password, senha, hash, secret
- Endpoints de health check ou debug expondo configuracoes internas (SECRET_KEY, credenciais)
- Log de dados sensiveis (numeros de cartao, senhas) no output
- Retorno de dados sensiveis apos operacoes de criacao ou atualizacao

**Impacto:** Qualquer consumidor da API tem acesso a dados que deveriam ser internos. Viola principios de seguranca (PCI-DSS para cartoes, etc.).

---

### 8. Tight Coupling / Global Mutable State

**Conceito:** Componentes fortemente acoplados via estado global mutavel ou dependencias diretas hardcoded.

**Sinais de deteccao:**
- Conexao de banco como variavel global mutavel compartilhada entre modulos
- Estado global mutavel exportado como modulo (caches, contadores)
- Import direto do modulo de banco dentro de funcoes de rota
- Uso de `self = this` ou workaround similar para contornar escopo
- Instanciacao de servicos com configuracao hardcoded ao inves de injetada

**Impacto:** Dificil testar com mocks. Estado compartilhado pode causar comportamento imprevisivel sob concorrencia. Mudancas em um modulo propagam efeitos colaterais.

---

### 9. Callback / Promise Nesting Hell

**Conceito:** Multiplas operacoes assincronas aninhadas em vez de encadeadas linearmente.

**Sinais de deteccao:**
- 4 ou mais niveis de funcoes aninhadas (callbacks, then chains, etc.)
- Contadores manuais para rastrear completude de operacoes paralelas
- Error handling inconsistente entre niveis de aninhamento
- Padrao onde o resultado de uma operacao assincrona imediatamente dispara outra, em cadeia profunda

**Impacto:** Codigo dificil de ler e manter. Erros em niveis internos sao dificeis de rastrear. Impossivel usar try/catch de forma efetiva.

---

## MEDIUM

### 10. N+1 Query Problem

**Conceito:** Queries ao banco executadas dentro de loops, gerando uma query por iteracao ao inves de uma unica query otimizada.

**Sinais de deteccao:**
- Execucao de queries dentro de loops (for, forEach, while, etc.)
- Para cada item de uma lista, uma nova query buscando dados relacionados
- Carregamento de associacoes um-a-um em vez de eager loading
- Queries separadas para dados relacionados que poderiam ser unidas com JOIN

**Impacto:** Performance degrada linearmente com o volume de dados. Com N itens, gera N+1 queries ao inves de 1.

---

### 11. Duplicated Code

**Conceito:** Logica identica ou quase identica repetida em multiplos lugares.

**Sinais de deteccao:**
- Funcoes quase identicas para entidades diferentes (mesma estrutura, tabela diferente)
- Blocos de tratamento de erro repetidos com padrao identico
- Logica de serializacao repetida em multiplos lugares
- Validacao duplicada entre operacoes de criacao e atualizacao
- Logica de verificacao (ex: overdue, status check) copiada em 3 ou mais arquivos

**Impacto:** Mudancas precisam ser replicadas em multiplos lugares. Facil esquecer um ponto de duplicacao ao corrigir um bug.

---

### 12. Inadequate Error Handling

**Conceito:** Tratamento de erros generico, ausente ou que engole excecoes silenciosamente.

**Sinais de deteccao:**
- Blocos catch/except sem tipo especifico de excecao (catch-all)
- Excecoes capturadas e engolidas sem log ou re-throw
- Erros retornados como texto simples em vez de formato estruturado
- Ausencia de tratamento de erros em operacoes criticas
- Mensagens de erro genericas que nao ajudam a identificar o problema

**Impacto:** Bugs reais podem ser escondidos silenciosamente. Debug dificultado pela falta de informacao util.

---

### 13. Deprecated API Usage

**Conceito:** Uso de funcoes ou metodos que foram marcados como deprecated ou removidos em versoes mais recentes das dependencias.

**Sinais de deteccao:**
- Funcoes de data/hora que retornam valores sem timezone quando ha alternativas com timezone
- Metodos de ORM que foram substituidos por novas APIs
- Drivers de banco em modo verbose/debug em producao
- Padroes assincronos obsoletos (callbacks quando async/await esta disponivel)
- Qualquer uso de API que a propria documentacao marca como deprecated ou legacy

**Impacto:** Gera warnings, pode quebrar ao atualizar dependencias, e muitas vezes indica um problema conceitual (ex: datas sem timezone).

---

## LOW

### 14. Poor Variable Naming

**Conceito:** Variaveis com nomes que nao comunicam seu proposito.

**Sinais de deteccao:**
- Variaveis de uma letra para dados importantes
- Abreviacoes obscuras que nao sao universalmente conhecidas
- Nomes genericos (data, result, item) onde nomes especificos seriam mais claros

**Impacto:** Dificulta a leitura e compreensao do codigo. Novos desenvolvedores precisam decifrar significados.

---

### 15. Magic Numbers / Magic Strings

**Conceito:** Valores literais espalhados pelo codigo sem constante nomeada ou explicacao.

**Sinais de deteccao:**
- Numeros sem explicacao contextual (thresholds, limites, multiplicadores)
- Strings de status ou categorias repetidas em multiplos arquivos
- Portas, tamanhos minimos, timeouts hardcoded como numeros soltos
- Condicoes baseadas em valores literais sem nome descritivo

**Impacto:** Dificil entender a regra de negocio. Mudancas exigem procura em todo o codigo.

---

### 16. Debug Artifacts in Production Code

**Conceito:** Configuracoes e saidas de debug deixadas em codigo de producao.

**Sinais de deteccao:**
- Flag de debug habilitada na configuracao da aplicacao
- Saida de console/print como mecanismo de logging
- Modo verbose de drivers ou bibliotecas ativado
- Stack traces expondo detalhes internos em respostas de erro

**Impacto:** Em producao, expoe informacoes internas e polui logs.

---

### 17. Unused Imports / Dead Code

**Conceito:** Modulos importados ou codigo que nunca e utilizado.

**Sinais de deteccao:**
- Modulos importados mas nao referenciados no codigo
- Funcoes ou variaveis definidas mas nunca chamadas
- Constantes declaradas mas nao utilizadas

**Impacto:** Polui o codigo e pode causar confusao sobre dependencias reais.

---

## Resumo

| # | Anti-Pattern | Severidade |
|---|-------------|------------|
| 1 | SQL Injection | CRITICAL |
| 2 | Hardcoded Credentials | CRITICAL |
| 3 | God Class / God File | CRITICAL |
| 4 | Unauthenticated Sensitive Endpoints | CRITICAL |
| 5 | Weak Cryptography | CRITICAL |
| 6 | Business Logic in Route Layer | HIGH |
| 7 | Sensitive Data Exposure in API | HIGH |
| 8 | Tight Coupling / Global State | HIGH |
| 9 | Callback / Promise Nesting Hell | HIGH |
| 10 | N+1 Query Problem | MEDIUM |
| 11 | Duplicated Code | MEDIUM |
| 12 | Inadequate Error Handling | MEDIUM |
| 13 | Deprecated API Usage | MEDIUM |
| 14 | Poor Variable Naming | LOW |
| 15 | Magic Numbers / Strings | LOW |
| 16 | Debug Artifacts in Production | LOW |
| 17 | Unused Imports / Dead Code | LOW |
