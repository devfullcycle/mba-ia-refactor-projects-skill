# Template do Relatório de Auditoria (Fase 2)

O relatório deve ser impresso no terminal **e** salvo em Markdown com a estrutura abaixo, sem omitir seções. Textos entre `<>` são placeholders.

## Regras

1. **Ordenação**: todos os CRITICAL, depois HIGH, MEDIUM e LOW. Dentro da mesma severidade, ordene pelo ID do catálogo.
2. **Numeração**: findings numerados sequencialmente (`F-01`, `F-02`, ...) após a ordenação.
3. **Localização exata**: `File:` sempre com caminho relativo à raiz do projeto + linha(s) conferidas com `cat -n`. Vários locais → separar por `, ` (ex.: `models.py:28, models.py:48-49, models.py:92`).
4. **Evidência**: até 3 linhas do código real (copiado, não parafraseado).
5. **Recommendation** referencia o padrão do playbook (`PB-xx`).
6. O **Summary** precisa bater com a contagem dos findings listados.
7. A seção **Deprecated APIs** é obrigatória — se não houver ocorrências, escreva `None detected` e as verificações feitas.
8. Termine com a pergunta de confirmação (a Fase 2 sempre pausa).

## Template

````markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome da pasta>
Stack:   <Linguagem> + <Framework versão>
Files:   <N> analyzed | ~<L> lines of code
Date:    <AAAA-MM-DD>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### F-01 [CRITICAL] <Nome do anti-pattern> (<AP-xx>)
File: <arquivo>:<linha(s)>
Evidence:
```<lang>
<trecho real>
```
Description: <o que acontece, em 1–2 frases>
Impact: <consequência concreta para segurança/manutenção/performance>
Recommendation: <ação concreta> (<PB-xx>)

### F-02 [HIGH] ...

...

## Deprecated APIs
| File:Line | Deprecated API | Modern replacement |
|---|---|---|
| <arquivo:linha> | <API> | <substituto> |

## Refactoring Plan (preview of Phase 3)
- Target structure: <árvore resumida>
- <Fxx, Fyy> → <PB-xx>: <transformação>
- Contract changes required for security: <lista ou "None">

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
````

## Exemplo de finding bem escrito

````markdown
### F-02 [CRITICAL] SQL Injection (AP-01)
File: models.py:28, models.py:47-50, models.py:109-111
Evidence:
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
```
Description: Queries montadas por concatenação de strings com dados vindos do request em 15 pontos do arquivo.
Impact: Bypass de login com `' OR '1'='1' --`, leitura e destruição de qualquer tabela.
Recommendation: Usar placeholders `?` com tupla de parâmetros em todas as queries (PB-01).
````

## Exemplo de finding mal escrito (evitar)

```markdown
### [HIGH] Código ruim
File: models.py
Description: O código tem problemas de SQL.
```
Falhas: sem ID/anti-pattern do catálogo, sem linha, sem evidência, sem impacto, sem recomendação acionável.
