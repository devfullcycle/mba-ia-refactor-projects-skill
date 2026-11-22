# Análise de projeto (Fase 1)

Objetivo: descobrir stack, banco, domínio e arquitetura **por evidência no código**, com um método que funciona para qualquer tecnologia. Não há tabela fixa de linguagens: se você reconhece a stack, confirme-a por evidência; se não reconhece, pesquise (ver [stack-research.md](stack-research.md)).

## 1. Linguagem

Método, em ordem de confiança:
1. **Manifesto de dependências**: arquivo na raiz (ou nas pastas de módulos) que declara dependências, versão da linguagem e scripts de build/execução. Identifique-o pelo papel, não pelo nome: lista de pacotes, descritor de projeto, arquivo de build.
2. **Extensões dominantes** dos arquivos-fonte (conte por extensão, ignorando dependências vendorizadas e saídas de build).
3. **Arquivo de ambiente/versionamento**: declarações de versão da linguagem/runtime, imagem de container (`FROM`/base), arquivos de configuração de ferramenta.
4. **Sintaxe do ponto de entrada**: confirme lendo.

Versão: onde o manifesto, arquivo de runtime ou container declarar. Não declarada → escreva "não declarada".
Várias linguagens: a de backend é a que contém o ponto de entrada do servidor.

## 2. Framework e dependências

1. Leia o manifesto: liste as dependências e **versões**; separe as estruturais (servidor web/roteamento, ORM/acesso a dados, autenticação, validação, CORS, logging, testes) das utilitárias.
2. **Confirme no código**: o framework de fato usado aparece nos **imports/uses** do ponto de entrada e dos arquivos de rota. Dependência declarada e nunca usada não é framework do projeto.
3. Dependência **importada mas não declarada** no manifesto é um achado.
4. Framework não reconhecido: leia a documentação oficial dele (Stack Profile) antes de seguir.

## 3. Banco de dados

1. **Dependências de driver/ORM** no manifesto.
2. **Strings de conexão**, arquivos de banco embutido, variáveis de ambiente de banco, serviços no arquivo de composição de containers.
3. **Entidades/tabelas**: definições de esquema (`CREATE TABLE`, classes mapeadas, migrations, seeds). Liste os nomes.
4. Registre **como a conexão é obtida** (global, por requisição, injetada); alimenta a auditoria (estado global, acoplamento).
5. Sem banco aparente: registre "nenhum / não detectado".

## 4. Domínio

Deduza em **uma linha** a partir dos nomes de entidades, rotas, arquivos e README. Se houver dúvida, escreva a hipótese e a evidência.

## 5. Ponto de entrada e execução

1. Candidatos: arquivos com nomes de bootstrap (principal, app, server, index, main) ou que **iniciam o servidor/escutam uma porta**.
2. **Comando de execução**: scripts do manifesto, README, descritor de container, arquivos de processo. Anote também **porta** e como o servidor é encerrado.
3. **Comandos de build/teste/lint**, se existirem.
4. Se nada indicar, pergunte ao usuário (não adivinhe).

## 6. Mapeamento de arquitetura

Para cada arquivo-fonte, classifique as responsabilidades que ele **realmente contém**:

| Responsabilidade | Sinais conceituais |
|---|---|
| Roteamento/Views | associação de método+caminho a um handler; registro de rotas |
| Controle/orquestração | código que trata a requisição e decide o fluxo |
| Regra de negócio | cálculos, regras, estados, decisões de domínio |
| Acesso a dados | construção/execução de consultas, uso de ORM/driver, transações |
| Configuração | constantes, segredos, URLs, portas, flags |
| Serialização/formatação | montagem da estrutura devolvida ao cliente |
| Infra/utilidades | logging, helpers, middlewares, autenticação |

Classifique a arquitetura:

| Classe | Critério |
|---|---|
| **Monolítica / sem camadas** | Poucos arquivos com 3+ responsabilidades; rotas com acesso a dados e regra |
| **Parcialmente em camadas** | Há pastas/módulos de camadas, mas há vazamento: regra na rota, consulta fora do model, config espalhada |
| **MVC adequado** | Camadas com dependências na direção correta, config e erros centralizados |

Descreva em uma linha factual.

## 7. Baseline de endpoints

Para cada rota/operação exposta: `MÉTODO /caminho` → handler (arquivo:linha) → status e formato esperados (do código e de documentação/coleções de requisições existentes). Essa lista prova, na Fase 3, que o contrato foi preservado. **Uso interno: não a imprima na Fase 1**; só a contagem aparece em `Endpoints: <N> mapped`.

## 8. Limites de leitura

- Leia **todos** os arquivos-fonte quando couber (até ~40 arquivos ou ~5.000 linhas). Acima disso, priorize entrada, rotas, dados e config, amostre o resto e **declare** isso.
- Ignore dependências instaladas/vendorizadas, saídas de build, caches, binários, bancos embutidos e arquivos de lock.
