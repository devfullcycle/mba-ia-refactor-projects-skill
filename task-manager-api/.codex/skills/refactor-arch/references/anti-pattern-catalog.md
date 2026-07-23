# Catálogo de anti-patterns

Use este catálogo na Fase 2. Trate a severidade indicada como padrão e ajuste-a somente com justificativa baseada em alcance, exposição, explorabilidade e impacto no projeto analisado.

## Sumário

- Escala de severidade
- AP-01 a AP-03: segurança e autenticação
- AP-04 a AP-07: arquitetura, dependências e integridade
- AP-08 a AP-10: performance, duplicação e erros
- AP-11: APIs deprecated
- AP-12 a AP-14: integrações, configuração e higiene
- Checklist de fechamento

## Escala de severidade

- **CRITICAL:** compromete segurança, dados ou funcionamento, ou mistura completamente responsabilidades essenciais.
- **HIGH:** viola fortemente MVC/SOLID, integridade ou isolamento e torna mudanças e testes muito arriscados.
- **MEDIUM:** causa duplicação, validação inconsistente, performance degradada ou tratamento operacional inadequado.
- **LOW:** prejudica clareza, observabilidade ou configuração, sem risco imediato demonstrado.

Não conte sintomas da mesma causa como findings distintos sem vetores de impacto realmente independentes. Não eleve severidade só para atingir um mínimo.

## AP-01 — Injection ou execução arbitrária

**Severidade padrão:** `CRITICAL`

**Sinais:** concatenar/interpolar entrada em SQL; aceitar uma query do cliente; montar comando de shell, template ou expressão executável com dados não confiáveis; usar opção equivalente a `shell=true` sem isolamento.

**Confirmar:** trace a entrada até o sink e cite ambos. SQL com placeholders e parâmetros separados não é injection. Literais internos sem entrada controlável não bastam.

**Impacto:** leitura, alteração ou destruição de dados; execução remota; indisponibilidade.

**Correção:** parametrizar operações, restringir comandos por allowlist e remover interfaces de execução genérica. Relacionar a T02.

## AP-02 — Segredo ou dado sensível exposto

**Severidade padrão:** `CRITICAL`

**Sinais:** senha, token, chave privada/live ou connection string literal; segredo enviado a logs ou respostas; hashes de senha, cartão ou credenciais serializados; arquivo de ambiente real versionado.

**Confirmar:** não reproduza o valor; reporte apenas tipo, variável e localização. Placeholder evidente ou chave de teste documentada pode ser `LOW`/informativo.

**Impacto:** tomada de conta, acesso a serviços, fraude ou ampliação de vazamento.

**Correção:** rotacionar fora do escopo quando necessário, carregar por ambiente/secret manager e usar DTO público. Relacionar T01 e T09.

## AP-03 — Autenticação ou criptografia insegura

**Severidade padrão:** `CRITICAL`

**Sinais:** senha em texto puro, MD5/SHA rápido sem salt, Base64 como proteção, senha default, token previsível/falso, rota privilegiada sem autenticação/autorização.

**Confirmar:** diferencie hashing de senha de checksums não sensíveis. Verifique se middleware de autenticação é aplicado no prefixo superior antes de afirmar ausência.

**Impacto:** comprometimento de contas, escalada de privilégios e acesso indevido.

**Correção:** password hasher adaptativo, tokens verificados e autorização explícita. Relacionar T09.

## AP-04 — God class, module ou method

**Severidade padrão:** `HIGH`; elevar a `CRITICAL` apenas quando a concentração for total e provocar risco grave comprovado.

**Sinais:** o mesmo componente registra rotas, aplica negócio, persiste, configura infraestrutura, integra serviços e formata respostas; muitos domínios mudam pelo mesmo motivo; dependências numerosas e difíceis de substituir.

**Confirmar:** tamanho isolado não prova o finding. Cite responsabilidades distintas e seus intervalos.

**Impacto:** testes inseparáveis, alto raio de mudança e regressões frequentes.

**Correção:** separar por responsabilidade e domínio com direção explícita de dependências. Relacionar T03 e T04.

## AP-05 — Fat adapter/controller e violação de camadas

**Severidade padrão:** `HIGH`

**Sinais:** handler HTTP, CLI, mensagem, job, UI ou biblioteca contém queries, cálculos, transações, autorização complexa ou integração externa; Model usa objetos do protocolo/host; entry point executa regras de negócio.

**Confirmar:** parsing simples, chamada ao caso de uso e tradução para o contrato externo pertencem legitimamente ao adapter. Controllers podem orquestrar; não devem acumular detalhes de infraestrutura.

**Impacto:** acoplamento ao framework, duplicação e baixa testabilidade.

**Correção:** afinar adapters de entrada/saída e extrair caso de uso, Model/repository e presenter. Relacionar T03, T04 e T08.

## AP-06 — Estado global mutável ou dependência oculta

**Severidade padrão:** `HIGH`

**Sinais:** conexão/cache/lista global compartilhada; singleton criado no import; `check_same_thread` ou equivalente contornando segurança; dependência concreta importada e impossível de substituir; ciclo de vida sem fechamento.

**Confirmar:** constante imutável ou pool thread-safe gerenciado pelo framework não é o mesmo problema. Descreva concorrência e ciclo de vida reais.

**Impacto:** vazamento entre requisições, corrida, transações cruzadas e testes frágeis.

**Correção:** injetar dependências e adotar escopo por request/operação. Relacionar T04 e T05.

## AP-07 — Operação não atômica ou integridade quebrada

**Severidade padrão:** `HIGH`

**Sinais:** múltiplos writes do mesmo caso de uso sem transação; commit intermediário; ausência de rollback; deleção deixa órfãos; integração falha depois da persistência sem compensação.

**Confirmar:** verifique garantias do ORM/driver e limites da transação. Operações externas podem exigir outbox/saga, não uma transação de banco impossível.

**Impacto:** estado parcial, cobrança/matrícula divergente e corrupção de dados.

**Correção:** criar fronteira transacional e testar falha intermediária. Relacionar T06.

## AP-08 — N+1 queries ou acesso repetitivo

**Severidade padrão:** `MEDIUM`

**Sinais:** query dentro de loop de entidades; busca individual repetida de relações; callback aninhado que consulta cada item; carregamento lazy durante serialização de coleção.

**Confirmar:** demonstre a fórmula aproximada de consultas, como `1 + 2N`. Loop pequeno e constante pode reduzir a severidade, não apagar o sinal.

**Impacto:** latência e carga crescem com o volume.

**Correção:** join, eager loading, consulta em lote ou mapa por IDs. Relacionar T07.

## AP-09 — Regra, validação ou serialização duplicada

**Severidade padrão:** `MEDIUM`

**Sinais:** mesmas condições, limites, status, mensagens ou DTOs repetidos em rotas; helper existente ignorado; criar e atualizar divergem sem regra de domínio que justifique.

**Confirmar:** código superficialmente parecido para regras diferentes não é duplicação. Cite ao menos dois locais e a regra comum.

**Impacto:** comportamento divergente e custo de mudança multiplicado.

**Correção:** extrair validator, policy, presenter ou caso de uso reutilizável. Relacionar T08.

## AP-10 — Tratamento de erro inadequado

**Severidade padrão:** `MEDIUM`

**Sinais:** `except`/`catch` genérico que silencia erro; callback ignora `err`; resposta de sucesso apesar de falha; stack trace/SQL/segredo retornado; status e envelopes inconsistentes; `print` no lugar de logging operacional.

**Confirmar:** handler global pode existir fora do arquivo analisado. `catch` amplo na fronteira é aceitável quando traduz e registra corretamente.

**Impacto:** falso sucesso, vazamento interno e incidentes difíceis de diagnosticar.

**Correção:** erros tipados, tradução central e logging estruturado. Relacionar T10.

## AP-11 — API deprecated ou legado incompatível

**Severidade padrão:** `MEDIUM`; usar `HIGH` se houver remoção iminente ou falha comprovada, e `LOW` se a substituição for cosmética.

**Sinais:** warning explícito; símbolo marcado como deprecated na documentação; API removida na versão resolvida; dependência sem suporte; padrão antigo com substituto oficial.

**Confirmação obrigatória:** registre (1) símbolo e linhas, (2) versão efetiva do runtime/pacote, (3) fonte primária — documentação, changelog ou warning local — e (4) substituto. Sem esses quatro itens, rotule `candidato a confirmar` e não conte como finding confirmado. Não dependa apenas da memória.

**Procedimento estático:** examine manifests/locks, imports e usos; busque notas de depreciação já presentes nas dependências/documentação local sem ler árvores vendorizadas inteiras. Faça consulta externa apenas quando permitida e cite fonte primária. Não atualize pacote na Fase 2.

**Impacto:** warnings, incompatibilidade em upgrade e risco de segurança por runtime sem suporte.

**Correção:** substituir conforme documentação e adicionar teste de compatibilidade. Relacionar T11.

## AP-12 — I/O externo bloqueante ou frágil

**Severidade padrão:** `MEDIUM`

**Sinais:** integração externa direta no caminho de execução; ausência de timeout; retry cego; dado sensível em log; SDK concreto acoplado ao controller.

**Confirmar:** chamadas rápidas ainda precisam de timeout, mas filas podem ser desnecessárias em projetos pequenos. Verifique se adapter/middleware já provê resiliência.

**Impacto:** request preso, duplicidade de efeito e indisponibilidade em cascata.

**Correção:** adapter injetável, timeout, idempotência e execução assíncrona quando justificada. Relacionar T04, T06 e T10.

## AP-13 — Magic values e configuração dispersa

**Severidade padrão:** `LOW`; elevar se o literal for segredo, política crítica ou causar comportamento incorreto.

**Sinais:** portas, URLs, flags, limites, percentuais e status repetidos; debug habilitado no código; ambiente exigindo edição de fonte.

**Confirmar:** constantes locais autoexplicativas e estáveis podem ser adequadas. Diferencie configuração operacional de invariantes do domínio.

**Impacto:** baixa legibilidade e implantação arriscada.

**Correção:** módulo de configuração para ambiente e constantes nomeadas para domínio. Relacionar T01 e T08.

## AP-14 — Higiene e legibilidade deficientes

**Severidade padrão:** `LOW`

**Sinais:** imports/código mortos, nomes crípticos, branches redundantes, funções sem foco, comentários contraditórios, logging por `print` sem contexto.

**Confirmar:** nomes curtos de índices locais podem ser idiomáticos. Não transforme preferência estética em finding sem custo de manutenção demonstrável.

**Impacto:** revisão lenta, dependências obscuras e diagnóstico inconsistente.

**Correção:** remover código morto, renomear por intenção e usar logging estruturado. Relacionar T08/T10 quando fizer parte de mudança já aprovada.

## Checklist de fechamento da auditoria

- Examinar todos os 14 IDs ou registrar por que não se aplicam.
- Confirmar cada path e intervalo contra o arquivo atual.
- Redigir evidência sem revelar segredos.
- Deduplicar por causa raiz.
- Recalibrar severidade pelo impacto concreto.
- Ordenar `CRITICAL → HIGH → MEDIUM → LOW`.
- Fazer a checagem de deprecated APIs mesmo quando o resultado for negativo.
- Não prometer que todos os anti-patterns serão removidos; priorizar escopo seguro e aprovado.
