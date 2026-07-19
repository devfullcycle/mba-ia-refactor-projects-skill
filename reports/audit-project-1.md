================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code

Summary
CRITICAL: 6 | HIGH: 2 | MEDIUM: 4 | LOW: 1

MVC Adherence: 4/10 (Parcial)
  Models:       parcial — models.py isola acesso a dados, mas concentra regra de negócio, múltiplos domínios e SQL inseguro
  Views/Routes: parcial — app.py mapeia rotas, porém traz handlers com lógica e SQL inline (index, /admin/*)
  Controllers:  parcial — controllers.py orquestra e valida, mas com try/except duplicado e efeitos colaterais (notificações via print)
  Separation:   violada — estado global de conexão, SQL concatenado e ausência de camadas de config/middlewares

Findings

[CRITICAL] SQL Injection generalizado por concatenação de strings
File: models.py:28,48-49,58-60,68,92,110,127-128,140,149-150,155,158-160,164-165,174,188,192,220,224,280,289-297
Description: Praticamente toda a camada de dados monta SQL concatenando input do usuário diretamente na query (ex.: "SELECT * FROM produtos WHERE id = " + str(id); "... WHERE email = '" + email + "'"; busca com termo/categoria via concatenação). Nenhuma query usa parâmetros vinculados.
Impact: Injeção de SQL trivial em busca, login e CRUD — leitura, alteração e destruição arbitrária do banco; bypass de autenticação no login_usuario.
Recommendation: Usar exclusivamente queries parametrizadas (placeholders "?" com tupla de parâmetros) em toda a camada de dados. Ver AP-03 e o playbook de refatoração.

[CRITICAL] Endpoint /admin/query executa SQL arbitrário do cliente
File: app.py:59-78
Description: A rota POST /admin/query recebe uma string SQL no corpo e a executa diretamente (cursor.execute(query)), com commit para não-SELECT, sem qualquer autenticação.
Impact: Qualquer cliente pode ler ou destruir todo o banco (DROP/DELETE/UPDATE) e exfiltrar dados sensíveis (inclusive senhas).
Recommendation: Remover o endpoint. Necessidades administrativas devem passar por operações específicas, parametrizadas e autenticadas. Ver AP-13.

[CRITICAL] Endpoint /admin/reset-db destrutivo e sem autenticação
File: app.py:47-57
Description: POST /admin/reset-db apaga todas as tabelas (DELETE FROM itens_pedido/pedidos/produtos/usuarios) sem verificação de identidade ou permissão.
Impact: Qualquer um pode zerar o banco de produção em uma única requisição.
Recommendation: Remover em produção ou proteger com autenticação/role administrativa e confirmação explícita. Ver AP-13.

[CRITICAL] Senhas em texto puro (armazenamento, comparação e exposição)
File: models.py:83,99,105-131; database.py:75-83
Description: Senhas são gravadas em texto puro (criar_usuario e seed), comparadas em texto puro no login (WHERE senha = '...') e ainda retornadas nas respostas de get_todos_usuarios e get_usuario_por_id (campo "senha" no JSON).
Impact: Vazamento direto de credenciais em qualquer breach ou em uma simples chamada GET /usuarios; sem qualquer proteção criptográfica.
Recommendation: Fazer hash com salt (werkzeug.security / bcrypt / argon2) na criação e verificar hash no login; nunca serializar o campo senha nas respostas. Ver AP-04.

[CRITICAL] SECRET_KEY hardcoded e vazada pelo /health
File: app.py:7; controllers.py:289
Description: A SECRET_KEY está fixa no código ("minha-chave-super-secreta-123") e é devolvida em texto no payload do endpoint /health (junto com debug e db_path).
Impact: Segredo exposto em todo clone/commit e publicado por um endpoint público, permitindo forjar/assinar dados da aplicação.
Recommendation: Carregar a chave de variável de ambiente num módulo de config; remover secret_key/debug do retorno de /health. Ver AP-02.

[CRITICAL] God module e violação estrutural do MVC
File: models.py:1-315; controllers.py:1-293; database.py:14-84
Description: models.py concentra acesso a dados, regra de negócio (cálculo de total/estoque em criar_pedido, regras de desconto em relatorio_vendas) e múltiplos domínios (produtos, usuários, pedidos, relatórios) num único arquivo; database.py mistura conexão, DDL (CREATE TABLE) e seed; não há camadas de config nem middlewares. A separação existente é apenas por tipo técnico, não por responsabilidade.
Impact: Impossível testar/reusar regras em isolamento; qualquer mudança arrisca quebrar domínios não relacionados; viola SRP e o padrão MVC-alvo.
Recommendation: Separar models por entidade (produto/usuario/pedido), extrair regra de negócio para model/service, isolar config e schema, adicionar middleware de erro. Ver AP-01 e 04-mvc-guidelines.

[HIGH] Estado global mutável de conexão com check_same_thread=False
File: database.py:4-10
Description: A conexão SQLite é guardada numa variável global (db_connection) reatribuída via singleton implícito e aberta com check_same_thread=False para contornar o compartilhamento entre threads do Flask.
Impact: Condições de corrida entre requisições concorrentes, acoplamento forte e código praticamente impossível de testar/paralelizar.
Recommendation: Conexão por request (factory) injetada no composition root; usar app context (g) ou pool. Ver AP-05.

[HIGH] Regra de negócio na camada de dados
File: models.py:133-169,235-273
Description: criar_pedido faz validação de estoque, cálculo de total e baixa de estoque diretamente no acesso a dados; relatorio_vendas embute regras de desconto por faixa de faturamento. A lógica de domínio está presa ao SQL.
Impact: Regra não reutilizável nem testável isoladamente; controllers ficam anêmicos e a regra fica acoplada ao banco, dificultando manutenção e evolução.
Recommendation: Extrair a regra para model/service de pedido e de relatório, deixando o acesso a dados separado. Ver AP-06.

[MEDIUM] Query N+1 na listagem de pedidos
File: models.py:187-199,219-231
Description: get_pedidos_usuario e get_todos_pedidos iteram sobre pedidos e, para cada um, abrem novo cursor para buscar itens e, dentro deste, mais uma query por item para o nome do produto.
Impact: Número de queries cresce linearmente com pedidos e itens; degradação de performance e carga desnecessária no banco.
Recommendation: Substituir por JOINs (pedidos + itens_pedido + produtos) ou por consultas agregadas com IN (...). Ver AP-08.

[MEDIUM] criar_pedido sem transação atômica
File: models.py:133-169
Description: A criação de pedido faz INSERT em pedidos, múltiplos INSERT em itens_pedido e UPDATE de estoque com um único commit ao final, sem transação explícita nem rollback em caso de falha no meio.
Impact: Falha parcial deixa dados inconsistentes (pedido sem itens, estoque baixado sem pedido); integridade comprometida.
Recommendation: Envolver a operação numa transação explícita com rollback no erro (try/except + BEGIN/ROLLBACK ou context manager). Ver AP-12.

[MEDIUM] Duplicação massiva de código
File: models.py:9-22,77-87,203-233; controllers.py:6-12,21-22,etc.
Description: O mapeamento row→dict de produto/usuário/pedido é repetido em várias funções; get_pedidos_usuario e get_todos_pedidos são quase idênticas; o bloco try/except que formata erro 500 é copiado em praticamente todos os controllers.
Impact: Manutenção multiplicada e risco de divergência silenciosa entre cópias.
Recommendation: Extrair serializadores/reutilizar funções de query e centralizar o tratamento de erro num middleware. Ver AP-10.

[MEDIUM] Debug ligado e servidor de desenvolvimento em produção
File: app.py:8,88; controllers.py:208-210,248-250
Description: DEBUG=True na config e debug=True no app.run(host="0.0.0.0"), expondo o debugger interativo do Werkzeug; efeitos colaterais (envio de email/sms/push, notificações) são simulados com print espalhados pelos controllers.
Impact: Debugger interativo exposto permite execução de código remoto; logs poluídos e lógica de notificação acoplada ao controller sem tratamento real.
Recommendation: Controlar debug por ambiente (config), servir via WSGI de produção e mover notificações para um serviço dedicado com logging estruturado. Ver AP-16.

[LOW] Magic numbers nas regras de desconto
File: models.py:256-262
Description: As faixas e taxas de desconto (10000/0.1, 5000/0.05, 1000/0.02) estão como literais soltos no meio do cálculo de relatorio_vendas.
Impact: Intenção de negócio obscura e mudança arriscada/duplicada.
Recommendation: Extrair para constantes nomeadas em config ou no topo do módulo. Ver AP-14.

================================
Total: 13 findings
================================
