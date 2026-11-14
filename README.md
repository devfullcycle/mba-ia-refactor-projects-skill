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

- Decisões de design: como estruturou o SKILL.md e os arquivos de referência
- Quais anti-patterns incluiu no catálogo e por quê
- Como garantiu que a skill é agnóstica de tecnologia
- Desafios encontrados e como resolveu

## 📈 *Resultados*

- Resumo dos relatórios de auditoria dos 3 projetos (quantos findings por severidade em cada)
- Comparação antes/depois da estrutura de cada projeto
- Checklist de validação preenchido para cada projeto
- Screenshots ou logs mostrando as aplicações rodando após refatoração
- Observações sobre como a skill se comportou em stacks diferentes

## ⏯️ *Como Executar*

- Pré-requisitos (a ferramenta escolhida, instalada e configurada)
- Comandos para executar a skill em cada projeto
- Como validar que a refatoração funcionou

```markdown
## Checklist de Validação

### Fase 1 - Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade

### Fase 2 - Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 - Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente
```
