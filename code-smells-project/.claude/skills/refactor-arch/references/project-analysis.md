# Project Analysis Heuristics

## Language Detection

Identifique a linguagem procurando por:

- **Extensao dos arquivos fonte** — a extensao predominante indica a linguagem
- **Arquivos de gerenciamento de dependencias** — cada linguagem tem seus arquivos caracteristicos (requirements.txt, package.json, go.mod, pom.xml, Cargo.toml, etc.)
- **Sintaxe dos imports** — o padrao de import revela a linguagem
- **Estrutura do projeto** — algumas linguagens tem convencoes obrigatorias

## Framework Detection

Procure nos arquivos de dependencia pela presenca de frameworks web:

- Leia o arquivo de dependencias e identifique frameworks web listados
- Verifique a versao declarada na dependencia
- Confirme com os imports nos arquivos fonte — o framework principal aparecera na maioria dos arquivos

## Database Detection

Procure por:

- Strings de conexao — qualquer string contendo protocolos de banco (sqlite://, postgresql://, mongodb://, mysql://, etc.)
- Imports de drivers de banco — modulos especificos para conexao com banco de dados
- Arquivos de banco — presenca de arquivos .db, .sqlite, etc.
- Uso de ORM — imports de ORMs indicam qual banco esta em uso
- Banco em memoria — strings como `:memory:` indicam banco que nao persiste dados

## Architecture Classification

Leia todos os arquivos fonte e classifique:

1. **Monolitica** — Poucos arquivos contendo toda a logica misturada (routes, queries, business rules)
2. **Parcial** — Existe alguma separacao de diretorios mas a logica vaza entre camadas
3. **MVC** — Separacao adequada entre Models, Views/Routes e Controllers
4. **Outra** — Organizacao diferente que nao se encaixa nas categorias acima

### Sinais para classificar:
- Routes chamando banco diretamente → separacao inadequada
- Arquivos com multiplas entidades/domínios → God File
- Lógica de negócio misturada com definição de rotas → violacao de camada
- Models manipulando request/response → violacao de responsabilidade
- Se o projeto ja tem estrutura parcial, avalie o que funciona e o que precisa melhorar

## Domain Detection

Leia as definicoes de rotas, nomes de modelos e endpoints para determinar o dominio de negocio:
- Produtos, pedidos, carrinho → E-commerce
- Cursos, matriculas, pagamentos → LMS / Educacao
- Tasks, projetos, categorias → Gestao de tarefas/projetos
- Posts, comentarios, usuarios → Social / Blog
- Ou qualquer outro dominio identificado pelos nomes das entidades

## Dependency Mapping

Liste todas as dependencias externas do arquivo de gerenciamento de pacotes do projeto.
Nao inclua dependencias de desenvolvimento.

## Source File Analysis

- Conte todos os arquivos de codigo fonte (excluindo: .git, node_modules, __pycache__, vendor, .venv, arquivos de lock, arquivos de dados)
- Estime o total de linhas de codigo
- Liste cada arquivo com sua funcao resumida
