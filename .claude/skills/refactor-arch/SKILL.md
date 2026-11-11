---
name: refactor-arch
description: Analisa, audita e refatora automaticamente projetos legados para o padrão arquitetural MVC de forma agnóstica a tecnologia.
---

# Skill: refactor-arch (Refatoração Arquitetural Automatizada para MVC)

Você é um Arquiteto de Software Especialista encarregado de analisar, auditar e refatorar codebases legadas para o padrão **MVC (Model-View-Controller)**. 

Ao ser ativado, você DEVE executar rigorosamente as **3 Fases Sequenciais** descritas abaixo, consultando os arquivos de referência localizados neste mesmo diretório (`.claude/skills/refactor-arch/`).

---

## FASE 1 — Análise de Projeto

1. Leia o arquivo `analise_heuristica.md` para aplicar as heurísticas de detecção.
2. Analise a raiz do projeto atual e identifique:
   - **Linguagem & Framework:** (ex: Python/Flask, Node.js/Express, etc.)
   - **Banco de Dados & ORM/Driver:** (ex: SQLite3, SQLAlchemy, PostgreSQL, etc.)
   - **Mapeamento da Arquitetura Atual:** Lista de arquivos, diretórios e estimativa de acoplamento.
   - **Domínio da Aplicação:** (ex: E-commerce, LMS, Task Manager).
3. **Output da Fase 1:** Imprima no terminal um resumo claro da análise no formato:
   ```text
   ==================================================
   FASE 1: RESUMO DA ANÁLISE DE PROJETO
   ==================================================
   - Language: <Linguagem>
   - Framework: <Framework>
   - Dependencies: <Dependencies>
   - Domain: <Domínio>
   - Architecture: <Monolithic / Partially Organized / Modular>
   - Database: <BD / Driver>Auditoria
   - Source Files: <Quantidade de arquivos analisados>
   - DB tables: <Tabela(s) detectada(s)>
   - Diagnóstico Inicial: <Breve avaliação da estrutura>
   ==================================================
   ```

## FASE 2 — Auditoria e Diagnóstico
Leia os arquivos catalogo_anti_patterns.md e template_relatorio.md.

Faça uma varredura estática profunda no código-fonte do projeto cruzando-o contra o Catálogo de Anti-patterns (buscando no mínimo os anti-patterns catalogados e uso de APIs deprecated).

Classifique cada problema por severidade: CRITICAL, HIGH, MEDIUM ou LOW.

Garanta que o diretório reports/ exista na raiz do projeto e salve o relatório gerado preenchendo o template oficial em: reports/audit-project-<id>.md.

PAUSA E CONFIRMAÇÃO OBRIGATÓRIA:

Imprima uma síntese dos achados no console.

PARALISE A EXECUÇÃO e exiba a mensagem:

⚠️ Atenção: A auditoria foi concluída. O relatório detalhado foi gerado em reports/audit-project-<id>.md.
Deseja prosseguir com a Fase 3 (Refatoração Automática para MVC)? [y/N]

NÃO altere nem crie nenhum arquivo de código antes de receber a confirmação explícita do usuário.

## FASE 3 — Refatoração Arquitetural Automática e Validação

1. **Leitura de Diretrizes:** Leia o arquivo `playbook_refatoracao.md` e a `guideline_arquitetura_mvc.md`.
2. **Execução Modular Estruturada:** Com base nas Fases 1 e 2, execute a refatoração progressiva para o padrão MVC:
   - **Camada Model:** Centralize toda a persistência e acesso a dados em `src/models/`.
   - **Camada Controller / Services:** Isole as regras de negócio em controllers dedicados.
   - **Camada Routes / Views:** Reestruture as rotas para despacharem para os controllers.
   - **Configurações e Segurança:** Extraia credenciais para `.env` em `src/config/`.
3. **Validação de Contrato:** Assegure que o código refatorado mantenha o contrato funcional original da aplicação (mantendo endpoints, métodos HTTP e estruturas de resposta compatíveis).
4. **Validação Prática de Execução:** 
   - **Boot da Aplicação:** O agente deve subir a aplicação localmente para testar a integridade da inicialização.
   - **Teste de Endpoints:** O agente deve executar chamadas reais de teste (ex: via comandos HTTP/PowerShell ou script de teste) nos endpoints principais (públicos e protegidos) para comprovar que o contrato funcional e a segurança (tokens/middlewares) estão funcionando perfeitamente.
5. **Output da Fase 3:** Imprima no terminal o relatório resumindo as alterações e os resultados dos testes funcionais realizados.

   ```text
   ==================================================
   FASE 3: RESUMO DA REFATORAÇÃO MVC CONCLUÍDA
   ==================================================
   - Arquivos Criados: <Lista arquivos de diretórios e novos>
   - Arquivos Modificados: <Lista arquivos de refatorados>
   - Anti-patterns Corrigidos: <Resumo dos principais problemas resolvidos>
   - Status: Refatoração estrutural concluída com sucesso!
   ==================================================