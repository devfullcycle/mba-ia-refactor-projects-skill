# Guidelines agnósticas de MVC

Use estas regras na Fase 3. Avalie papéis, fronteiras e direção das dependências; não exija nomes de diretórios, annotations, classes-base ou APIs de um framework específico.

## Sumário

- Aplicabilidade e equivalências
- Direção de dependências
- Models
- Views e adapters
- Controllers e casos de uso
- Infraestrutura, configuração e erros
- Bootstrap/composition root
- Estrutura lógica portátil
- Preservação de contratos
- Checklist

## Aplicabilidade e equivalências

Use MVC como separação de responsabilidades, não como molde literal:

| Tipo de unidade | View | Controller | Model |
|---|---|---|---|
| HTTP/RPC | rota, serializer, presenter | handler/caso de uso | domínio + repository |
| CLI | parser e formatter | command handler | domínio + gateway |
| Mensageria | consumer/producer adapter | message handler | domínio + store |
| Job/pipeline | adapter de trigger e output | job/stage orchestrator | domínio + state access |
| GUI | tela/view-model adapter | action/controller | domínio + data model |
| Biblioteca/plugin | API/export adapter | application service | domínio/estado |

Se o ecossistema já usa arquitetura equivalente — camadas, ports-and-adapters, application/domain/infrastructure — preserve a convenção e documente o mapeamento. Não introduza View artificial, camada vazia ou transporte inexistente apenas para cumprir um nome.

Se MVC conflitar com a natureza da unidade, proponha a separação equivalente no relatório e obtenha aprovação antes da escrita.

## Direção de dependências

Adote o fluxo lógico:

```text
external input → View/adapter → Controller/use case → Model/domain → data port
                                      ↓
                                 service port

domain result/error → Controller → View/presenter → external output
```

- Faça adapters externos dependerem do núcleo, nunca o inverso.
- Proíba domínio, Model e repository port de importar objetos do protocolo ou host.
- Injete stores, relógio, identidade e integrações no bootstrap.
- Use interfaces/ports quando elas isolarem infraestrutura, habilitarem teste ou representarem fronteira real; não crie abstração vazia.

## Models

Models devem:

- representar entidades, value objects, estado e invariantes;
- encapsular persistência por abstração coerente com a codebase;
- receber dados independentes do protocolo externo;
- proteger campos sensíveis e controlar DTOs públicos;
- oferecer operações em lote e consistência transacional quando necessário.

Models não devem:

- escolher status/código de protocolo;
- ler request, mensagem, stdin, UI ou objeto do framework;
- formatar resposta externa;
- disparar integração concreta sem port;
- depender de conexão global mutável sem lifecycle.

Model pode significar domínio mais repository/data mapper. Preserve o estilo nativo se as responsabilidades continuarem separadas.

## Views e adapters

Views/adapters devem:

- declarar ou implementar a interface externa;
- extrair e validar a forma básica da entrada;
- converter entrada em comando/DTO;
- chamar Controller/use case;
- traduzir resultado e erro para o contrato externo;
- delegar representação repetida a presenter/serializer/formatter.

Views/adapters não devem:

- executar query ou controlar transação;
- calcular regra comercial;
- construir client/conexão concreta por operação;
- duplicar validação de domínio;
- expor erro interno ou segredo.

## Controllers e casos de uso

Controllers devem:

- orquestrar o fluxo da aplicação;
- aplicar autorização e validação contextual;
- chamar Models/repositories e service ports;
- definir unidade transacional ou coordenação de efeitos;
- devolver resultado independente do framework quando possível;
- ser testáveis com doubles nas fronteiras externas.

Controllers não devem:

- montar query de persistência;
- depender de singleton ou configuração oculta;
- registrar interfaces ou iniciar host;
- incorporar SDK/client concreto;
- concentrar domínios não relacionados.

Preserve nomes idiomáticos como application service, command/query handler, use case, interactor ou processor quando desempenharem esse papel.

## Infraestrutura e integrações

- Implemente ports para persistência, fila, filesystem, rede, cache, relógio e identidade.
- Coloque SDKs, retries, timeouts, serialização técnica e tradução de falhas nos adapters.
- Garanta idempotência e compensação quando efeitos externos não participarem de uma transação comum.
- Use doubles ou ambientes isolados; nunca valide disparando efeito real irreversível.

## Configuração

- Leia ambiente/configuração externa em um módulo próprio e valide campos obrigatórios.
- Mantenha segredos fora do código, relatório, log e payload.
- Separe configuração operacional de constantes do domínio.
- Permita override de teste para stores e serviços temporários.
- Não prescreva formato de configuração; use a convenção segura do ecossistema detectado.

## Tratamento de erros

- Modele erros de domínio/aplicação com significado.
- Traduza-os para protocolo somente na View/adapter ou handler central da interface.
- Registre falhas operacionais com contexto e sem dados sensíveis.
- Preserve códigos, envelopes e tipos de erro contratados, salvo correção aprovada.
- Garanta rollback/compensação antes de publicar falso sucesso.

## Bootstrap e composition root

O bootstrap deve:

1. carregar e validar configuração;
2. construir infraestrutura e adapters;
3. construir repositories, serviços e Controllers;
4. registrar interfaces e error handlers;
5. iniciar ou expor a unidade.

Mantenha-o pequeno e explícito. Evite migration, seed, acesso remoto ou outro efeito irreversível durante import/load. Em ecossistemas com container de injeção, trate o módulo de registrations como composition root.

## Estrutura lógica portátil

Adapte às convenções locais:

```text
<source-root>/
├── configuration/             # ou mecanismo nativo equivalente
├── domain-or-model/           # entidades e invariantes
├── application-or-controller/ # casos de uso/orquestração
├── interface-or-view/         # HTTP, CLI, eventos, UI, serializers
├── infrastructure/            # stores e integrações concretas
├── error-mapping/
└── bootstrap/                 # composition root/entry point
```

Esses são papéis, não nomes obrigatórios. Preserve namespaces, packages, projects, modules e convenções existentes quando já expressarem a mesma separação.

## Preservar contratos

Antes de mover código, congele por interface:

- identidade da operação;
- autenticação/autorização;
- entrada e defaults;
- saída, código/status e erro;
- efeitos persistentes/externos;
- ordenação, timing ou compatibilidade relevantes.

Faça mudanças estruturais sem redesenhar a interface. Quando corrigir vulnerabilidade exigir mudança observável, destaque o conflito e obtenha aprovação específica; compatibilidade não justifica preservar exposição grave silenciosamente.

## Estratégia incremental

1. Adicione testes de caracterização para comportamento seguro existente.
2. Extraia configuração e crie seams de dependência.
3. Isole persistência e integrações.
4. Mova orquestração para Controllers/use cases.
5. Afine Views/adapters e centralize erros.
6. Remova caminhos antigos somente após equivalência comprovada.

Prefira passos pequenos a reescrita total. Não crie camadas que apenas repassem chamadas sem proteger uma responsabilidade.

## Checklist de conformidade

- [ ] O mapeamento MVC/equivalente está explícito por tipo de unidade.
- [ ] Models não conhecem protocolo externo e protegem invariantes/dados.
- [ ] Views/adapters limitam-se a transporte, formato e apresentação.
- [ ] Controllers orquestram sem query ou SDK concreto.
- [ ] Infraestrutura depende de ports do núcleo.
- [ ] Configuração e segredos ficam fora da lógica.
- [ ] Erros são traduzidos na fronteira correta.
- [ ] Bootstrap somente compõe e inicia/expõe.
- [ ] Operações multi-efeito possuem atomicidade, idempotência ou compensação.
- [ ] Contratos públicos aprovados permanecem compatíveis.
- [ ] Cada unidade possui validação de build/load, teste e boot quando aplicável.
