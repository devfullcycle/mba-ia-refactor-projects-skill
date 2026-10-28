---
name: refactor-arch-analyze
description: Fase 1 - Análise. Descobre linguagem, framework, banco, arquitetura, domínio e gera reports/analysis-<projeto>.md. Somente leitura.
---

# refactor-arch-analyze — Fase 1 (Análise)

Objetivo: responder com evidência, **em que linguagem, com que framework, sobre qual banco e com que arquitetura** o projeto é escrito. Gerar relatório reutilizável sem modificar código-fonte.

## Referências a ler

Leia integralmente antes de aplicar:
- `../refactor-arch/references/stack-detection.md`
- `../refactor-arch/references/architecture-detection.md`
- `../refactor-arch/references/report-template.md`

## Passo 1 — Delimitar o escopo

Descubra a raiz do projeto (diretório de trabalho atual, a menos que o usuário indique outro caminho).

Excluir sempre: `.git`, `node_modules`, `__pycache__`, `.venv`, `venv`, `env`, `.env`, `dist`, `build`, `target`, `out`, `vendor`, `.next`, `.nuxt`, `coverage`, `.mypy_cache`, `.pytest_cache`, `.tox`, `bin`, `obj`, `*.egg-info`, `logs`, `tmp`.

Coletar:
- Lista de manifestos presentes (até profundidade 3)
- Árvore de diretórios até profundidade 3

```bash
find . -maxdepth 3 -type f \
  \( -name 'package.json' -o -name 'requirements*.txt' -o -name 'pyproject.toml' \
     -o -name 'setup.py' -o -name 'Pipfile' -o -name 'poetry.lock' -o -name 'go.mod' \
     -o -name 'pom.xml' -o -name 'build.gradle*' -o -name 'Cargo.toml' \
     -o -name 'Gemfile' -o -name 'composer.json' -o -name '*.csproj' -o -name '*.sln' \
     -o -name 'pubspec.yaml' -o -name 'mix.exs' -o -name 'CMakeLists.txt' \) \
  -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/.venv/*'

find . -maxdepth 3 -type d \
  -not -path '*/node_modules*' -not -path '*/.git*' -not -path '*/__pycache__*' \
  -not -path '*/.venv*' -not -path '*/venv*' -not -path '*/dist*' -not -path '*/build*' \
  | sort
```

## Passo 2 — Detectar a linguagem
Seguir `stack-detection.md`. Tratar bindings quando manifesto misto. Se sem manifesto, contar extensões. Reportar também linguagem de markup/template quando presente.

## Passo 3 — Detectar o framework
Cruzar dependências com dicionário. **Confirmar no código** (import/uso). Se declarado mas não usado → reportar "dependência declarada, uso não confirmado no código".

## Passo 4 — Detectar banco de dados e integrações
Identificar driver/ORM, string de conexão/variáveis. Classificar relacional/NoSQL/em memória/não identificável. Listar integrações relevantes.

## Passo 5 — Mapear a arquitetura
Usar `architecture-detection.md`:
- **5a** Evidência estrutural (pastas candidatas a camada)
- **5b** Evidência de código (entrypoint + 2-4 arquivos representativos) — distinguir roteamento vs regra de negócio vs acesso a dados

## Passo 6 — Classificar a arquitetura
Classificar em: Flat/Monolítico-desestruturado, Monolítico em camadas, MVC, Modular monolith, Clean/Hexagonal, Base de código única, ou Indeterminado. Coletar entrypoint(s), tamanho/LOC, testes, CI/CD, containerização, config.

## Passo 7 — Inferir o domínio
Derivar do que existe nas rotas/entidades/reais (não do nome da pasta).

## Passo 8 — Emitir o resultado
Aplicar `report-template.md`:
1. **Bloco de resumo no terminal** (caixa monoespaçada)
2. **Arquivo `reports/analysis-<nome-do-projeto>.md`** com evidências, inventário, tabela de camadas, candidatos a anti-pattern para Fase 2

Nome do projeto = nome do diretório de trabalho. Criar `reports/` se não existir. **Não sobrescrever sem avisar** — numerar se já existir.

## Passo 9 — Fechar
Incluir bloco "Notas e lacunas". Não inventar confiança.

## Regras
- **Somente leitura + relatório**. Não editar/mover/deletar código-fonte.
- **Evidência obrigatória** com arquivo:linha quando aplicável.
- **Confiança explícita** (alta/média/baixa) nas detecções.
- **Agnóstico de tecnologia**.
