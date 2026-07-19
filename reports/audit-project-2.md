================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express 4
Files:   3 analyzed | ~180 lines of code

Summary
CRITICAL: 4 | HIGH: 3 | MEDIUM: 4 | LOW: 2

MVC Adherence: 1/10 (Monolítico)
  Models:       ausente — SQL cru espalhado nos handlers; nenhuma entidade encapsula dados/regra
  Views/Routes: ausente — rotas declaradas dentro de um método da God Class, misturadas à lógica
  Controllers:  ausente — não há camada de orquestração; handlers fazem tudo inline
  Separation:   violada — AppManager concentra DB, regra de negócio e roteamento (God Class)

Findings

[CRITICAL] God Class — AppManager concentra dados, regra e roteamento
File: src/AppManager.js:4-141
Description: A classe AppManager faz tudo: abre a conexão SQLite, cria schema e seeds, declara TODAS as rotas e implementa a regra de negócio de checkout e relatório inline. É um único módulo com responsabilidades de model, controller e router de múltiplos domínios (users, courses, enrollments, payments).
Impact: Impossível testar qualquer regra em isolamento; qualquer alteração arrisca quebrar toda a aplicação; viola SRP e o padrão MVC por completo.
Recommendation: Separar em camadas — models/repositórios por entidade, controllers magros por recurso, rotas isoladas e composition root fino. (AP-01)

[CRITICAL] Segredos hardcoded no código-fonte
File: src/utils.js:1-7
Description: O objeto config traz credenciais e chaves em texto literal: dbPass "senha_super_secreta_prod_123", paymentGatewayKey "pk_live_1234567890abcdef", smtpUser e dbUser. São segredos de produção versionados no repositório.
Impact: Qualquer clone/commit expõe as credenciais; comprometimento imediato do gateway de pagamento e do banco em caso de vazamento do código.
Recommendation: Mover para variáveis de ambiente (process.env) carregadas em um módulo de config; remover os valores do fonte e rotacionar as chaves expostas. (AP-02)

[CRITICAL] Senha em texto puro e hashing caseiro inseguro
File: src/utils.js:17-23
Description: badCrypto faz um "hash" caseiro (base64 repetido, truncado em 10 chars) — não é criptografia real e é trivialmente reversível/colidível. Além disso, o seed insere senha em texto puro ('123') em src/AppManager.js:18, e o checkout usa badCrypto para novos usuários (src/AppManager.js:68).
Impact: Vazamento direto de credenciais dos usuários em caso de breach; senhas efetivamente sem proteção.
Recommendation: Usar hashing forte com salt (bcrypt ou argon2); nunca armazenar/seedar senha em texto puro. (AP-04)

[CRITICAL] Endpoints administrativos e destrutivos sem autenticação
File: src/AppManager.js:80,131
Description: GET /api/admin/financial-report expõe receita e lista de alunos/pagamentos de todos os cursos sem qualquer auth. DELETE /api/users/:id apaga usuário sem autenticação nem autorização.
Impact: Qualquer um lê todo o faturamento e dados de alunos, e pode deletar usuários arbitrariamente — vazamento de dados sensíveis e destruição de dados.
Recommendation: Proteger com autenticação/autorização (role admin); mover a rota destrutiva para trás de middleware de auth. (AP-13)

[HIGH] Regra de negócio presa no handler de rota (sem controllers/models)
File: src/AppManager.js:28-137
Description: Os handlers de checkout e relatório abrem cursores, executam SQL, aplicam regras de pagamento/matrícula e formatam a resposta — tudo inline no arquivo de rotas. Não há model nem controller.
Impact: Viola MVC e SRP; a regra não pode ser reusada nem testada isoladamente; handlers gigantes e frágeis.
Recommendation: Extrair regra para services/models; controller apenas orquestra; rota apenas mapeia caminho+método. (AP-06)

[HIGH] Estado global mutável compartilhado
File: src/utils.js:9-10
Description: globalCache e totalRevenue são variáveis de módulo mutáveis, compartilhadas por toda a app (globalCache alimentado em logAndCache, src/utils.js:12-15). A conexão de banco também vive presa na God Class (src/AppManager.js:7), compartilhada implicitamente.
Impact: Acoplamento forte, condições de corrida entre requisições, e código praticamente impossível de testar/paralelizar.
Recommendation: Injeção de dependência; escopo de cache/estado por request ou store dedicado; injetar a conexão no composition root. (AP-05)

[HIGH] Callback hell / I/O sequencial aninhado sem camadas
File: src/AppManager.js:37-77,83-128
Description: O checkout aninha db.get → db.get → db.run → db.run → db.run em callbacks; o relatório aninha db.all → forEach → db.all → forEach → db.get → db.get. Usa `self = this` (linha 26) para driblar escopo e espalha o tratamento de erro por dezenas de callbacks.
Impact: Ilegível, difícil tratar erro de forma consistente, propenso a bugs de fluxo e sem separação de camadas.
Recommendation: Promisify o driver sqlite3 (ou util.promisify) e usar async/await; extrair repositório/serviço; transações explícitas. (AP-07)

[MEDIUM] Query N+1 no relatório financeiro
File: src/AppManager.js:89-125
Description: Para cada curso busca enrollments, e para cada enrollment dispara uma query de usuário e outra de pagamento — uma consulta por item em vez de um JOIN/agregação.
Impact: Número de queries cresce linearmente com alunos/matrículas; degradação de performance e carga desnecessária no banco.
Recommendation: Substituir por um JOIN entre courses/enrollments/users/payments (ou IN(...)) agregando no banco. (AP-08)

[MEDIUM] Falta de transação e dados órfãos na deleção
File: src/AppManager.js:50-62,131-137
Description: O checkout faz INSERTs relacionados (enrollments, payments, audit_logs) sem transação — falha no meio deixa estado inconsistente. DELETE /api/users/:id apaga o usuário mas deixa enrollments e payments órfãos (a própria resposta admite: "ficaram sujos no banco").
Impact: Integridade referencial quebrada e estado inconsistente do banco.
Recommendation: Envolver operações relacionadas em transação; deletar em cascata (ou bloquear delete com dependências); ON DELETE CASCADE / limpeza explícita. (AP-12)

[MEDIUM] Dados sensíveis em log (número de cartão + chave do gateway)
File: src/AppManager.js:45
Description: console.log imprime o número completo do cartão (cc) e a paymentGatewayKey a cada checkout.
Impact: Vazamento de PAN de cartão e da chave de pagamento nos logs — violação de compliance (PCI) e superfície de ataque.
Recommendation: Remover o log; se necessário, logar apenas dados mascarados via logging estruturado, sem segredos nem PAN. (AP-16)

[MEDIUM] Validação de entrada ausente/insuficiente no checkout
File: src/AppManager.js:29-35
Description: O checkout lê usr/eml/pwd/c_id/card do body sem validar tipo ou formato; a checagem (linha 35) nem exige pwd e não valida formato de e-mail nem numérico de c_id/card. Sem schema de validação.
Impact: Erros 500, dados inconsistentes (ex.: e-mail inválido persistido) e superfície para abuso.
Recommendation: Validar por schema na entrada (ex.: joi/zod) com retornos 400 claros; normalizar tipos. (AP-09)

[LOW] Nomenclatura críptica de variáveis
File: src/AppManager.js:29-33
Description: Variáveis de negócio nomeadas u, e, p, cid, cc; campos do contrato usr/eml/pwd/c_id abreviados.
Impact: Leitura mais lenta e maior chance de bug por mal-entendido.
Recommendation: Renomear para nomes intencionais (name, email, password, courseId, card). (AP-15)

[LOW] Regra de pagamento em valor mágico
File: src/AppManager.js:47
Description: A aprovação do pagamento é decidida por cc.startsWith("4") ("PAID"/"DENIED") — string mágica com significado de negócio embutido no handler.
Impact: Intenção obscura e regra de negócio escondida num literal, difícil de manter/alterar.
Recommendation: Extrair para um gateway/serviço de pagamento nomeado com constantes de status. (AP-14)

================================
Total: 13 findings
================================
