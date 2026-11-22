# Template do relatório de auditoria (Fase 2)

Use **exatamente** esta estrutura. Seções em inglês (padrão do output); conteúdo descritivo no idioma do usuário.

## Regras de preenchimento

- **Ordem dos findings: CRITICAL → HIGH → MEDIUM → LOW.** Dentro do mesmo nível, do mais impactante ao menos.
- **Arquivo e linha exatos**: `caminho/arquivo:12` ou `:12-48`. Várias ocorrências do mesmo problema: um finding, com lista de locais (até 5, depois "+N ocorrências").
- **Campos obrigatórios por finding**: título com ID do catálogo, File, Description, Impact, Recommendation (citando o padrão `PB-xx`).
- **Mascare segredos**: `'minh****'`, nunca o valor completo.
- **Contagens** do Summary devem bater com os findings listados.
- **APIs deprecated** entram como findings `AP-13` na lista de Findings (obsoleto → substituto → fonte ou "a verificar" na Description). **Sem seção própria.**
- **Saída exata, sem extras**: não adicione seções (fontes, Stack Knowledge, Positive Observations, Refactoring Plan), tabelas, comentários ou perguntas além da confirmação final. Esse conteúdo fica interno.
- Não inclua findings que você não confirmou lendo o código.
- Termine **sempre** com a linha de confirmação.

## Estrutura

````markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome da pasta>
Stack:   <linguagem> + <framework + versão> (<banco>)
Files:   <N> analyzed | ~<L> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] <AP-xx Nome do anti-pattern>
File: <arquivo>:<inicio>-<fim>
Description: <o que foi encontrado, concreto, com o trecho relevante resumido>
Impact: <consequência prática: segurança, teste, manutenção>
Recommendation: <ação objetiva> (playbook: PB-xx)

### [CRITICAL] ...

### [HIGH] <AP-xx Nome>
File: ...
Description: ...
Impact: ...
Recommendation: ...

### [MEDIUM] ...

### [LOW] ...

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
````

## Exemplo mínimo (nível de detalhe esperado)

````markdown
### [CRITICAL] AP-02 Hardcoded Credentials
File: <entrypoint>:8
Description: Chave de assinatura de sessão definida como 'minh****' direto no código-fonte, versionada no repositório.
Impact: Quem tem acesso ao repositório consegue forjar sessões/tokens.
Recommendation: Ler de configuração externa e falhar na inicialização se ausente (playbook: PB-02).

### [MEDIUM] AP-09 N+1 Query
File: <model>:120-135
Description: Para cada pedido da lista é executada uma consulta adicional para buscar os itens (consulta dentro de laço).
Impact: 1+N consultas por requisição; latência cresce com o volume.
Recommendation: Buscar os itens em uma consulta (JOIN ou conjunto de IDs) e agrupar em memória (playbook: PB-08).
````
