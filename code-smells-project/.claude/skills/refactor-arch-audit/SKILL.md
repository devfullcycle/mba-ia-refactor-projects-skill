---
name: refactor-arch-audit
description: Fase 2 - Auditoria. Varre código contra catálogo de anti-patterns com evidência e severidade, gera reports/audit-<projeto>.md e PAUSA aguardando confirmação para Fase 3. Somente leitura.
---

# refactor-arch-audit — Fase 2 (Auditoria)

Objetivo: auditar o código contra o catálogo de anti-patterns, com evidência arquivo:linha, severidade e recomendações. **Não modificar código.** Pausar para confirmação antes da refatoração.

## Pré-requisitos
- `reports/analysis-<nome-do-projeto>.md` deve existir (gerado pela Fase 1).

## Referências a ler
Leia integralmente antes de aplicar:
- `../refactor-arch/references/anti-patterns.md`
- `../refactor-arch/references/audit-report-template.md`

## Passo 1 — Preparar
1. Ler `reports/analysis-<projeto>.md`. Usar seção "O que a Fase 2 deve auditar" como ponto de partida, mas **verificar cada candidato no código**.
2. Definir escopo: todos os arquivos de código identificados na análise, excluindo `.git`, `node_modules`, `__pycache__`, `.venv`, `venv`, `env`, `.env`, `dist`, `build`, `target`, `out`, `vendor`, `.next`, `.nuxt`, `coverage`, `.mypy_cache`, `.pytest_cache`, `.tox`, `bin`, `obj`, `*.egg-info`, `logs`, `tmp`.

## Passo 2 — Varredura por anti-pattern
Aplicar regras do `anti-patterns.md`:
- **SEC-01** SQL Injection (f-string/concatenação/% em queries)
- **SEC-02** Credenciais hardcoded
- **SEC-03** Criptografia fraca
- **SEC-04** Rota sem auth (POST/PUT/DELETE/PATCH)
- **SEC-05** XSS
- **SEC-06** Log sensível
- **ARCH-01** Lógica de negócio no Controller (>10 linhas com regra)
- **ARCH-02** Acesso a dados no Controller
- **ARCH-03** Model com responsabilidades duplas
- **PERF-01** N+1
- **QUAL-01** God Class (>300 LOC Python / >400 LOC JS/TS com múltiplos domínios)
- **QUAL-02** Validação ausente
- **QUAL-03** Tratamento de erro genérico
- **QUAL-04** Estado global mutável
- **QUAL-05** Dependência morta
- **QUAL-06** Sem migrations
- **QUAL-07** Config hardcoded
- **QUAL-08** Sem testes
- **DEP-01** Uso de APIs deprecated

## Passo 3 — Confirmar e classificar
Para cada candidato:
1. **Confirmar no código** - ler trecho exato. Sem evidência, descartar.
2. **Atribuir severidade** conforme catálogo.
3. **Registrar arquivo:linha** exato ou intervalo.
4. **Agrupar** - mesmo anti-pattern no mesmo arquivo = um achado com múltiplos locais.
5. **Contextualizar** - considerar contexto (health-check vs pagamento).

## Passo 4 — Montar o mapa de calor
Contar achados por severidade por arquivo.

## Passo 5 — Emitir o relatório
Aplicar `audit-report-template.md`:
1. **Bloco de resumo no terminal** agrupado por severidade (CRITICAL→LOW), com IDs e localizações
2. **Arquivo `reports/audit-<nome-do-projeto>.md`** com achados detalhados (evidência + impacto + recomendação + exemplo), mapa de calor, por categoria, recomendações prioritárias, notas/limitações

Nome do projeto = diretório de trabalho. Criar `reports/` se não existir. **Não sobrescrever sem avisar** - numerar se já existir.

**PAUSAR PARA CONFIRMAÇÃO.** Após emitir o relatório, apresentar achados ao usuário e aguardar confirmação explícita ("sim", "prossiga", "aplique a Fase 3", etc.) antes de iniciar Fase 3.

## Regras
- **Somente leitura + relatório**. Não editar/mover/deletar código-fonte.
- **Evidência obrigatória** com arquivo:linha exato.
- **Severidade não inflada**. Contexto importa.
- **Não duplicar** - agrupar por arquivo.
- **Pausar sempre** ao final.
- **Agnóstico de tecnologia**.
