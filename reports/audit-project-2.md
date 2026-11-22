================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express ^4.18.2 (SQLite em memória via sqlite3 ^5.1.6)
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 3 | HIGH: 4 | MEDIUM: 5 | LOW: 3

## Findings

### [CRITICAL] AP-01 God Class / God File
File: src/AppManager.js:4-139 (+ src/utils.js:1-25)
Description: A classe AppManager (nome genérico) cria a conexão com o banco (:7), define schema e seed (:10-23), registra as rotas (:25-137), contém regra de negócio de checkout (:43-64), consultas SQL, orquestração e serialização das respostas. O handler de checkout tem ~50 linhas com 7 níveis de callbacks aninhados e o de relatório ~50 linhas com 5 níveis. utils.js também é um "Utils" genérico que mistura config, cache, log e criptografia.
Impact: Impossível testar ou evoluir uma responsabilidade isoladamente; qualquer mudança arrisca quebrar as demais.
Recommendation: Separar em config, database, models, services/controllers, routes e composition root (playbook: PB-01).

### [CRITICAL] AP-02 Hardcoded Credentials
File: src/utils.js:2-5
Description: O objeto config contém literais versionados no código: dbPass = 'senha****', paymentGatewayKey = 'pk_l****' (chave live do gateway de pagamento), dbUser = 'admi****' e smtpUser = 'no-r****'. A senha do usuário seed ('123') também está em texto puro no código (src/AppManager.js:18).
Impact: Quem tem acesso ao repositório obtém credenciais de produção e a chave do gateway de pagamento.
Recommendation: Ler de variáveis de ambiente, falhar no boot se ausentes e documentar em um .env.example sem valores reais (playbook: PB-02).

### [CRITICAL] AP-04 Autenticação e segurança de dados quebradas
File: src/utils.js:17-23; src/AppManager.js:68, 80, 131-137
Description: (1) badCrypto não é hash de senha: concatena 2 caracteres do base64 da própria senha 10.000 vezes e trunca em 10 caracteres (determinístico, sem sal, reversível por inspeção); usado em src/AppManager.js:68. (2) A senha padrão "123456" é atribuída quando pwd não é enviado (:68). (3) GET /api/admin/financial-report (:80) e DELETE /api/users/:id (:131) são operações administrativas/destrutivas sem autenticação ou autorização.
Impact: Senhas facilmente recuperáveis; qualquer cliente anônimo lê o relatório financeiro com nomes de alunos e apaga usuários.
Recommendation: Usar hash adequado com sal (bcrypt/scrypt, async), exigir senha no cadastro e proteger rotas administrativas com middleware de autenticação/autorização (playbook: PB-04).

### [HIGH] AP-05 Lógica de negócio em Controllers/Rotas
File: src/AppManager.js:28-78, 80-129
Description: Os handlers de rota contêm a regra de pagamento (cartão iniciado em "4" é PAID, senão DENIED, :46-48), criação implícita de usuário (:66-72), matrícula, pagamento, auditoria e o cálculo de receita do relatório (:108-110). O usuário é criado (:69) antes de o pagamento ser validado (:48), deixando usuário órfão quando o pagamento é recusado.
Impact: Regra de negócio não reutilizável nem testável sem HTTP; ordem das operações gera inconsistência de dados.
Recommendation: Mover para services (checkout/relatório) e deixar o controller só com entrada → serviço → resposta (playbook: PB-05).

### [HIGH] AP-06 Estado global mutável e acoplamento sem injeção de dependência
File: src/utils.js:9-15, 25; src/AppManager.js:7; src/app.js:8
Description: globalCache e totalRevenue são variáveis mutáveis de módulo (utils.js:9-10), escritas por logAndCache (:12-15) e exportadas; AppManager instancia o próprio banco no construtor (src/AppManager.js:7) e app.js cria o AppManager (:8); as rotas acessam config via import direto.
Impact: Estado compartilhado entre requisições, sem possibilidade de substituir o banco ou o cache em testes.
Recommendation: Injetar conexão/repositórios nos serviços a partir de um composition root e remover o cache global ou encapsulá-lo (playbook: PB-06).

### [HIGH] AP-07 Violação de camadas
File: src/AppManager.js:37-129, 133
Description: Todas as rotas executam SQL direto com o driver (this.db.get/run/all) e montam a resposta HTTP no mesmo callback; não existe camada de acesso a dados nem de serviço.
Impact: Troca de banco ou mudança de contrato exige alterar as rotas; sem testes de unidade possíveis.
Recommendation: Criar models/repositórios para o acesso a dados e controllers finos (playbook: PB-01, PB-05).

### [HIGH] AP-08 Exposição de dados sensíveis em logs
File: src/AppManager.js:45; src/utils.js:13
Description: O checkout loga o número completo do cartão e a chave live do gateway ('pk_l****') via console.log. Mantido em HIGH porque a chave já está registrada em AP-02.
Impact: Número de cartão (PAN) e chave de pagamento vazam para logs/coletores de logs.
Recommendation: Remover o log do cartão e da chave; logar apenas identificadores mascarados (playbook: PB-02, PB-07).

### [MEDIUM] AP-09 Consultas N+1
File: src/AppManager.js:83-127
Description: O relatório executa 1 consulta de cursos e, para cada curso, uma de matrículas (:92); para cada matrícula, uma de usuário (:104) e uma de pagamento (:106).
Impact: 1 + C + 2·E consultas por requisição; latência cresce com o volume de dados.
Recommendation: Buscar cursos, matrículas, usuários e pagamentos com um JOIN (ou conjunto de IDs) e agrupar em memória (playbook: PB-08).

### [MEDIUM] AP-10 Validação de entrada ausente ou inconsistente
File: src/AppManager.js:29-35, 132
Description: O checkout só verifica a presença de usr, eml, c_id e card; não valida formato de e-mail, tipo de c_id, formato do cartão nem pwd (opcional, ganha "123456" como padrão). O :id do DELETE não é validado.
Impact: Dados inválidos chegam ao banco e à lógica de pagamento; contas criadas com senha previsível.
Recommendation: Validar o corpo e os parâmetros em uma camada dedicada, respondendo 400 uniformemente (playbook: PB-09).

### [MEDIUM] AP-11 Tratamento de erros ausente ou espalhado
File: src/AppManager.js:57-61, 92-93, 104-106, 133-135, 35-84
Description: Erros do banco são ignorados em vários pontos: o erro da consulta de matrículas (:92) não é checado antes de usar enrollments.length (:93), causando exceção não tratada; erros de user/payment (:104, :106) e do log de auditoria (:57) são descartados; o DELETE ignora err e sempre responde com sucesso (:133-135). Respostas de erro são montadas manualmente em cada rota, como texto puro, enquanto o sucesso é JSON; não há tratador global.
Impact: Falhas silenciosas, processo derrubado por exceção em callback e formatos de erro inconsistentes.
Recommendation: Propagar erros e centralizar em um middleware de erro com formato único e sem vazar detalhes internos (playbook: PB-07).

### [MEDIUM] AP-12 Código duplicado
File: src/AppManager.js:95-99, 117-122
Description: O bloco de "fechar o curso" (report.push, coursesPending--, if === 0 res.json) aparece duplicado nos dois ramos do relatório.
Impact: Correções precisam ser feitas em dois pontos; risco de divergência.
Recommendation: Eliminar a contagem manual ao reestruturar o relatório com uma consulta e uma agregação única (playbook: PB-10).

### [MEDIUM] AP-13 API obsoleta / estilo legado (callbacks aninhados)
File: src/AppManager.js:37-128
Description: Callbacks aninhados do sqlite3 (até 7 níveis) com contadores manuais de pendências, em vez de async/await sobre promessas. Substituto: async/await com wrapper de promessas (ou Express 5, que trata promessas rejeitadas). Fonte: guia de tratamento de erros do Express (Express 4 não captura erros em handlers assíncronos); status de deprecation oficial do padrão callback do sqlite3 a verificar. Nenhuma API do Express 4.18 deprecated foi encontrada no código.
Impact: Código difícil de ler e de tratar erros corretamente; manutenção cara.
Recommendation: Encapsular o driver em funções assíncronas baseadas em promessas e usar async/await com repasse de erros ao middleware (playbook: PB-11).

### [LOW] AP-14 Magic numbers e strings soltas
File: src/AppManager.js:46, 48, 68, 108, 113, 19; src/utils.js:19, 22
Description: Literais sem nome: "PAID"/"DENIED", prefixo "4" do cartão, senha padrão "123456", 'Unknown', e em utils.js o 10000 de iterações e o 10 de truncamento.
Impact: Significado implícito e valores repetidos difíceis de alterar com segurança.
Recommendation: Extrair para constantes nomeadas (playbook: PB-12).

### [LOW] AP-15 Nomenclatura ruim
File: src/AppManager.js:29-33, 52, 90, 102; src/utils.js:17
Description: Variáveis de 1-3 letras (u, e, p, cid, cc, c, enr, enrId, self) e nomes pouco descritivos (badCrypto, AppManager, processPaymentAndEnroll com múltiplas responsabilidades). Campos do contrato (usr, eml, pwd, c_id, card) devem ser preservados.
Impact: Legibilidade reduzida e intenção obscura.
Recommendation: Renomear internamente para nomes descritivos, mantendo os campos externos (playbook: PB-12).

### [LOW] AP-16 Código morto e logging inadequado
File: src/AppManager.js:2, 59; src/utils.js:3-5, 10, 12-15, 25
Description: totalRevenue importado e exportado, nunca usado; dbUser, dbPass e smtpUser nunca lidos; globalCache exportado e nunca lido; console.log de debug no lugar de logger (src/AppManager.js:45, utils.js:13); callback da auditoria recebe err sem usá-lo (src/AppManager.js:57).
Impact: Ruído, falsa impressão de funcionalidades inexistentes e logs poluídos.
Recommendation: Remover o código não usado e usar um logger com níveis (playbook: PB-12).

================================
Total: 15 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
