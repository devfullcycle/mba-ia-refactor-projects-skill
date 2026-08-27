# Catálogo de Anti-Patterns e Code Smells

Este catálogo define os principais anti-patterns arquiteturais, problemas de segurança e qualidade de código, com seus respectivos sinais de detecção e classificação de severidade.

---

## 1. SQL Injection (Injeção de SQL)
* **Severidade**: **CRITICAL**
* **Sinais de Detecção**:
  - Uso de concatenação de strings (`+` ou f-strings) para inserir parâmetros de usuário diretamente em consultas SQL.
  - Exemplos: `cursor.execute("SELECT * FROM users WHERE id = " + str(id))` ou `cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")`.
* **Impacto**: Permite que atacantes extraiam, modifiquem ou deletem dados confidenciais do banco de dados e ganhem controle administrativo do sistema.

---

## 2. Pyramid of Doom (Callback Hell)
* **Severidade**: **CRITICAL**
* **Sinais de Detecção**:
  - Aninhamento excessivo de callbacks assíncronos (geralmente mais de 3 níveis de recuo lateral).
  - Uso intensivo de callbacks de sucesso/erro aninhados na camada de persistência.
* **Impacto**: Torna o código quase ilegível, extremamente difícil de manter, testar e capturar erros corretamente.

---

## 3. Falsa Criptografia / Hashing de Senha Inseguro
* **Severidade**: **CRITICAL**
* **Sinais de Detecção**:
  - Armazenamento de senhas em texto claro ou uso de algoritmos de codificação reversíveis como Base64 (ex: `Buffer.from(pwd).toString('base64')`).
  - Hashing manual fraco (ex: SHA-1 sem salt, MD5) para armazenar credenciais.
* **Impacto**: Vazamento massivo de senhas de usuários em caso de comprometimento do banco de dados.

---

## 4. God Class / God Module (Classe / Arquivo Deus)
* **Severidade**: **CRITICAL**
* **Sinais de Detecção**:
  - Um único arquivo ou classe contendo mais de 400 linhas e gerenciando conexões com o banco, declaração de tabelas, execução de queries, regras de negócio e formatação de respostas HTTP.
  - Violação completa de isolamento de domínios (ex: `models.py` manipulando produtos, usuários e pedidos simultaneamente).
* **Impacto**: Forte acoplamento; qualquer alteração em um domínio quebra os demais. Impossível testar em isolamento.

---

## 5. Hardcoded Credentials (Segredos no Código)
* **Severidade**: **CRITICAL**
* **Sinais de Detecção**:
  - Senhas, chaves de API, segredos de sessões (`SECRET_KEY`), ou credenciais SMTP declarados diretamente em strings ou objetos de configuração no código-fonte.
  - Exemplos: `app.config["SECRET_KEY"] = "minha-chave-super-secreta"` ou `paymentGatewayKey: "pk_live_..."`.
* **Impacto**: Vazamento de credenciais críticas ao subir o código para repositórios públicos ou privados.

---

## 6. Sensitive Data Exposure in Health Endpoints (Vazamento de Segredos no Health Check)
* **Severidade**: **CRITICAL**
* **Sinais de Detecção**:
  - Inclusão direta de chaves privadas, segredos criptográficos (`SECRET_KEY`), chaves de API ou senhas de banco na resposta JSON exposta por endpoints de status e saúde pública (ex: `/health`, `/status`, `/status-sistema`).
* **Impacto**: Usuários não autenticados podem descobrir segredos estruturais que dão acesso total à falsificação de sessões, assinaturas e dados de integridade da API.

---

## 7. Fat Controllers (Controllers / Rotas com Regras de Negócio Pesadas)
* **Severidade**: **HIGH**
* **Sinais de Detecção**:
  - Arquivos de rotas contendo regras de negócio complexas, cálculos financeiros, atualizações diretas de estoque, ou orquestração manual de notificações (e-mail, SMS).
* **Impacto**: Dificulta a reutilização de regras de negócio em outros canais (ex: CLI ou Tasks assíncronas) e impede testes unitários de lógica de domínio isolados da camada HTTP.

---

## 8. Query N+1 Problem (Consultas em Loop)
* **Severidade**: **MEDIUM**
* **Sinais de Detecção**:
  - Execução de consultas SQL dentro de loops interativos (`for`, `forEach`, `while`).
  - Buscar detalhes de um relacionamento (ex: buscar dados do usuário para cada matrícula obtida) individualmente em vez de usar `JOIN` ou pré-carregamento (`eager loading`).
* **Impacto**: Degradamento exponencial do tempo de resposta da API conforme o volume de dados cresce devido ao overhead de conexões de banco de dados.

---

## 9. Tratamento de Erros Genérico ou Ocultação de Exceções (Bare Except)
* **Severidade**: **MEDIUM**
* **Sinais de Detecção**:
  - Captura genérica de erros com `try ... except Exception:` ou `except:` em Python sem registrar o stack trace real ou levantar novamente o erro.
  - Rotas retornando mensagens de erro genéricas como `{"error": "Erro interno"}` sem logs adequados para diagnóstico de desenvolvimento.
* **Impacto**: Dificuldade extrema na resolução de bugs em produção, pois a causa raiz do erro é mascarada.

---

## 10. Uso de APIs Deprecated (Obsoletas)
* **Severidade**: **MEDIUM** ou **LOW**
* **Sinais de Detecção**:
  - **Python**: Uso de `datetime.utcnow()` ou `datetime.utcfromtimestamp()` (deprecated desde o Python 3.12, substituído por timezone-aware: `datetime.now(timezone.utc)`).
  - **Flask**: Uso de `app.before_first_request` (removido no Flask 2.3+).
  - **Node.js**: Uso do método obsoleto `express.bodyParser()` ou `new Buffer()`.
* **Impacto**: Incompatibilidade com versões mais recentes do runtime e pacotes, impedindo atualizações de segurança das bibliotecas.
