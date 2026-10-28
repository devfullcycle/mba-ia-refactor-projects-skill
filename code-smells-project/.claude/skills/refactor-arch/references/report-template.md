# Template de Relatório — Análise de Codebase

Dois artefatos: (1) bloco de resumo no terminal, (2) arquivo Markdown em `reports/`.

## 1. Bloco de resumo no terminal

Caixa monoespaçada, campos na ordem abaixo. Preencha com `—` quando não houver dado. Mantenha o formato de caixa (borda `=` de 32 chars) e o alinhamento.

````
================================
PHASE 1: PROJECT ANALYSIS
================================
Project:      code-smells-project
Language:     Python 3
Framework:    Flask 3.1.1
Dependencies: flask==3.1.1, flask-cors==5.0.1
Database:     SQLite (sqlite3)
Domain:       E-commerce API — produtos, pedidos, usuarios
Architecture: Flat / monolitico desestruturado — 4 arquivos na raiz, sem separacao de camadas
Entrypoint:   app.py
Source files: 4 files analyzed (~800 LOC)
Layers found: none (rotas, queries e logica convivem nos mesmos arquivos)
Tests:        none
Config:       hardcoded in code (no .env)
================================
````

Regras do bloco:
- **Não invente** campos. Se um campo não se aplica, use `—`.
- **Versões** só se estiverem declaradas no manifesto; se a lib não está instalada, escreva `3.1.1 (declarado)`.
- `Architecture` sempre seguido do motivo, em uma linha, com caminho de evidência.
- `Layers found` lista as camadas candidatas **confirmadas na leitura de código**, com `none` quando não houver.

Se o projeto tiver deployable múltiplo, acrescente linha `Deployables: N (paths...)`.

## 2. Arquivo `reports/analysis-<projeto>.md`

```markdown
# Análise de Codebase — <projeto>

> Gerado pela skill `refactor-arch` (Fase 1 — Análise).
> Data: <YYYY-MM-DD> | Raiz: <caminho>

## 1. Resumo

| Campo | Valor |
|---|---|
| Linguagem | ... |
| Framework | ... |
| Dependências | ... |
| Banco de dados | ... |
| Domínio | ... |
| Arquitetura | ... |
| Entrypoint | ... |
| Tamanho | ... |
| Testes | ... |
| Configuração | ... |

## 2. Evidências de detecção

### 2.1 Linguagem
- Manifest: `<caminho>` — <conteúdo relevante>
- Extensões: <contagem por extensão>
- **Veredito:** <linguagem> — confiança: <alta/média/baixa> (motivo)

### 2.2 Framework
- Dependências candidatas: <lista>
- Confirmado no código: `<arquivo>:<linha>` — <trecho/import>
- **Veredito:** <framework> <versão> — confiança: <...>

### 2.3 Banco de dados
- Driver/ORM: <...>
- String de conexão: `<arquivo>:<linha>`
- **Veredito:** <engine + tipo>

### 2.4 Domínio
- Rotas detectadas: <lista de rotas/recursos>
- Entidades: <lista>
- **Veredito:** <descrição em uma linha>

## 3. Inventário

```
<árvore de diretórios até 3 níveis, com arquivos-chave>
```

| Linguagem | Arquivos | LOC |
|---|---|---|
| Python | 4 | ~800 |

## 4. Arquitetura

### 4.1 Classificação
**Rótulo:** <um dos rótulos do architecture-detection.md>
**Justificativa:** <2-3 frases com caminhos>

### 4.2 Tabela de camadas

| Camada candidata | Diretório/arquivo | Existe? | Veredito |
|---|---|---|---|
| Model | `models.py` | sim | Contém queries SQL e regras de negócio — papel duplo |
| Controller | `controllers.py` | sim | Roteia e executa lógica de negócio |
| View | — | não | Ausente (API) |
| Service | — | não | Ausente |
| Config | — | não | Ausente |
| Middleware | — | não | Ausente |

Legenda do veredito: `adequada` | `parcial` | `papel violado` | `ausente` | `decorativa`

### 4.3 Leitura dos arquivos-chave
| Arquivo | LOC | Papel real | Observações |
|---|---|---|---|
| `app.py` | 40 | Entry point + rotas | ... |

## 5. Entrypoints, configuração e testes

- **Entrypoints:** <paths>
- **Configuração:** <env vars / hardcoded / arquivo>
- **Testes:** <presentes? qual framework?>
- **CI/CD:** <...>
- **Containerização:** <...>

## 6. Candidatos a anti-pattern

Achados que a própria leitura de código já revelou. **Não** são o relatório de auditoria — a Fase 2 confirma, classifica severidade e localiza linha exata.

| # | Sinal observado | Evidência | Anti-pattern candidato |
|---|---|---|---|
| 1 | ... | `arquivo:linha` | SQL Injection |

## 7. Notas e lacunas

- <o que não foi possível determinar, e o que seria necessário>
- <dependências declaradas mas não confirmadas no código>
- <referências da skill que não cobrem este ecossistema, se houver>
```

## 3. Regras de escrita

- **Todo item aponta para arquivo, com linha quando aplicável.**
- **Confiança explícita** nas detecções: alta (manifesto + código confirmam), média (só manifesto), baixa (só indício).
- **Sem achado sem evidência.** Se algo não pôde ser verificado, vai para "Notas e lacunas".
- **Fase 1 não emite severidade.** A escala CRITICAL/HIGH/MEDIUM/LOW pertence à auditoria (Fase 2).
- **Sem modificar código.** A skill só lê o projeto e escreve o relatório.

## 4. Nome do arquivo

`reports/analysis-<nome-do-projeto>.md`, onde `<nome-do-projeto>` é o nome do diretório de trabalho.

- `code-smells-project` → `reports/analysis-code-smells-project.md`
- `ecommerce-api-legacy` → `reports/analysis-ecommerce-api-legacy.md`

Se o arquivo já existir, **numere** (`analysis-<projeto>-2.md`) e avise o usuário — não sobrescreva silenciosamente.
