# Heurísticas agnósticas de análise de codebase

Use este guia somente na Fase 1. Descubra o ecossistema a partir dos artefatos locais; não use uma lista fechada de linguagens, frameworks, ferramentas ou layouts.

## Sumário

1. Delimitar escopo e unidades
2. Classificar evidências
3. Detectar linguagem, runtime e build
4. Detectar frameworks e interfaces
5. Detectar persistência e integrações
6. Mapear domínio e arquitetura
7. Inventariar contratos públicos
8. Descobrir comandos e validações
9. Preparar baseline sem escrita

## 1. Delimitar escopo e unidades

1. Resolva a raiz solicitada sem atravessar diretórios-pai.
2. Localize manifests, arquivos de workspace/solution, configurações de build, módulos, pacotes, entry points e descritores de deployment.
3. Separe cada unidade que possa ser construída, carregada, testada ou implantada independentemente. Trate monorepos e codebases poliglotas como conjuntos de unidades, não como uma stack única.
4. Leia regras de ignore e metadados do build para reconhecer dependências vendorizadas, caches, binários, cobertura, dados e fontes geradas. Exclua-os da contagem sem depender de nomes de diretórios pré-programados.
5. Conte apenas arquivos-fonte, configuração, migrations/schemas e testes efetivamente considerados. Registre a regra, inclusões, exclusões e total por unidade.

Se a ferramenta disponível não entender regras de ignore, derive as exclusões dos manifests e descritores de build. Não abra binários ou árvores vendorizadas para inferir arquitetura.

## 2. Classificar evidências

Use esta prioridade:

1. código executável, bootstrap e registros de interface;
2. manifests, locks e configuração de build;
3. configuração de runtime, deployment e persistência;
4. testes, fixtures e contract specifications;
5. documentação;
6. convenção inferida.

Cruze dois sinais independentes quando possível. Quando fontes divergirem, reporte a divergência e prefira o comportamento do código. Marque cada conclusão como:

- `HIGH`: comprovada por código mais manifesto/configuração ou por múltiplos pontos executáveis;
- `MEDIUM`: sustentada por um sinal forte ou vários indiretos;
- `LOW`: inferida por convenção, nome ou documentação não confirmada;
- `UNKNOWN`: evidência insuficiente; nunca adivinhe.

## 3. Detectar linguagem, runtime e build

Para cada unidade, examine:

- extensões e sintaxe dos fontes;
- shebangs, targets, módulos e imports;
- manifests e locks;
- plugins/SDKs do build;
- container, pipeline e configuração de deployment;
- scripts declarados e entry points.

Diferencie:

- linguagem de implementação;
- linguagem gerada ou de configuração;
- runtime/VM;
- compilador/SDK;
- ferramenta de build;
- gerenciador de dependências;
- versão declarada, resolvida e efetivamente executada.

Não conclua versão pela memória nem por uma convenção de diretório. Se a versão não estiver comprovada, registre `UNKNOWN`; isso afeta especialmente a verificação de APIs deprecated.

## 4. Detectar frameworks e interfaces

Identifique frameworks e bibliotecas pelo encadeamento:

```text
dependência declarada → import/referência → inicialização/composição → registro de interface → handler real
```

Classifique a função observada, sem depender do nome da tecnologia:

- host de aplicação ou servidor;
- interface HTTP/RPC;
- CLI;
- consumidor/produtor de mensagens;
- scheduler/job;
- GUI ou camada de apresentação;
- biblioteca pública/plugin;
- framework de persistência;
- injeção de dependência, middleware ou pipeline.

Uma dependência declarada mas nunca inicializada é suporte potencial, não framework confirmado. Em ecossistema desconhecido, leia o manifesto e siga os símbolos usados; não aplique heurísticas de outra linguagem.

## 5. Detectar persistência e integrações

Busque por comportamento, não por fornecedor:

- criação e ciclo de vida de conexões/clients;
- entidades, schemas, migrations e DDL;
- repositories, data mappers, queries e serialização;
- transações, commits, rollback, pooling e concorrência;
- filesystem, object storage e formatos persistidos;
- APIs externas, filas, e-mail, pagamentos, cache e busca.

Classifique cada mecanismo como embutido, remoto, em memória, arquivo, serviço ou desconhecido. Registre Models/entidades e stores apenas quando comprovados. Nunca copie valor de segredo; informe somente tipo, nome lógico e localização.

## 6. Mapear domínio e arquitetura

Infira domínio por consenso entre nomes de casos de uso, interfaces, entidades, eventos, schemas e testes. Use documentação apenas como complemento. Descreva o domínio em uma frase funcional e cite evidências.

Para cada módulo, marque responsabilidades observadas:

- entrada/apresentação;
- validação e autorização;
- orquestração de casos de uso;
- regra/invariante de domínio;
- persistência;
- integração externa;
- configuração/bootstrap;
- observabilidade e tratamento de erro.

Depois classifique a arquitetura pelo comportamento: monólito procedural, MVC, camadas, ports-and-adapters, modular, orientada a eventos, pipeline, plugin, híbrida ou desconhecida. Nomes de pastas não provam arquitetura.

Procure dependências entre módulos, ciclos, componentes centrais, estado global, inicialização por efeito de import/load e mistura de responsabilidades. Tamanho e complexidade são pistas, não findings sem evidência semântica.

## 7. Inventariar contratos públicos

Inventarie toda fronteira usada por consumidores, não apenas endpoints HTTP:

| Tipo | Identidade | Entrada | Saída/erro | Efeito | Evidência |
|---|---|---|---|---|---|
| HTTP/RPC | método + rota/operação | path/query/header/body | status + shape | persistência/integração | registro + handler |
| CLI | comando + opções | args/stdin/env | exit code/stdout/stderr | arquivos/rede | parser + dispatch |
| Mensagem/evento | tópico/tipo/schema | payload + headers | ack/evento/erro | estado/publicação | consumer/producer |
| Job | nome/schedule | parâmetros/contexto | resultado/erro | estado externo | scheduler + handler |
| Biblioteca/plugin | símbolo/interface | parâmetros/tipos | retorno/exceção | side effects | export + testes |
| UI/arquivo | ação/formato | interação/conteúdo | tela/formato/erro | estado | binding/parser |

Resolva prefixes, wrappers, middleware e dispatch indireto. Marque operações destrutivas ou externas para teste isolado. Preserve contratos inseguros apenas até explicitar o conflito; uma correção de segurança que muda comportamento exige aprovação própria.

## 8. Descobrir comandos e validações

Descubra, não invente, os comandos de:

1. restore/install;
2. code generation obrigatória;
3. build/compile/load;
4. análise estática, lint e tipos;
5. testes unitários, integração e contrato;
6. migrations/seed;
7. boot/readiness e shutdown.

Use scripts do projeto, pipelines e manifests antes da documentação e da convenção. Marque cada comando como `DISCOVERED`, `INFERRED` ou `VALIDATED`. Na Fase 1, não execute comando capaz de escrever, restaurar dependências, gerar fonte, iniciar unidade, migrar ou criar caches.

Para bibliotecas sem boot, defina build/load e suíte de testes como validação principal. Para múltiplas unidades, mantenha uma matriz de comandos por unidade.

## 9. Preparar baseline sem escrita

Produza em memória:

- árvore de unidades e relações;
- linguagens, runtimes, build e versões com confiança;
- frameworks, interfaces e persistências;
- domínio e mapa de responsabilidades;
- fluxo entre entrada, orquestração, domínio, dados e saída;
- contratos públicos por tipo;
- comandos descobertos por unidade;
- contagem auditável de fontes;
- lacunas, riscos e requisitos de isolamento para a Fase 3.

Se houver controle de versão, capture seu estado por meio da capacidade disponível. Caso contrário, use inventário e hashes somente-leitura. Não afirme que build, boot ou teste funciona antes da validação pós-aprovação.
