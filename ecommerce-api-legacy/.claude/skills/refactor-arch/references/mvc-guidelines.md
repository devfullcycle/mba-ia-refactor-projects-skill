# Guidelines de arquitetura: MVC alvo (Fase 3)

MVC para **APIs backend**: a "View" é a camada de **rotas/serialização** (mapeia entrada → controller e formata a resposta). Os **princípios** abaixo valem para qualquer stack; os **nomes, pastas e mecanismos** vêm do Stack Profile.

## Camadas e responsabilidades

| Camada | Faz | Não faz |
|---|---|---|
| **Config** | Lê configuração externa, define constantes, valida config obrigatória na inicialização | Lógica, acesso a dados |
| **Models** | Representam entidades e **acesso a dados** (consultas parametrizadas, ORM), regras intrínsecas da entidade | Conhecer requisição/resposta HTTP, formatar resposta |
| **Controllers** | Orquestram o caso de uso: validam entrada, chamam models/services, aplicam regra de negócio, decidem o resultado | Executar consultas; detalhes do framework de roteamento quando evitável |
| **Views / Routes** | Mapeiam método+caminho → controller; extraem parâmetros; serializam resposta e status | Regra de negócio, acesso a dados |
| **Middlewares / Error handling** | Tratamento centralizado de erros, autenticação, logging, CORS | Regra de negócio |
| **Entry point (composition root)** | Cria a aplicação, carrega config, instancia dependências, registra rotas e middlewares, inicia o servidor | Regra de negócio |

Se a regra de negócio crescer e for compartilhada, extraia uma camada de **services** mantendo o fluxo: Controller → Service → Model.

## Regra de dependência (sentido único)

```
Entry point ──► Routes(View) ──► Controllers ──► (Services) ──► Models ──► Banco
                                      ▲                            ▲
                                   Config  ◄──────── injetada ──────┘
```

- Models **não** dependem de controllers, rotas nem do framework web.
- Controllers **não** executam consultas e **não** dependem de rotas.
- Rotas **só** chamam controllers.
- Config não depende do restante; os demais a recebem (parâmetro ou leitura).
- Dependências (conexão, repositórios) são **criadas no entry point e injetadas**; evite singletons globais mutáveis.

## Estrutura-alvo (nomes conceituais)

```
<raiz-de-código>/
├── config/                  # configuração externa, constantes
├── models/                  # um por entidade/domínio
├── views-ou-routes/         # um por domínio (ou um arquivo se pequeno)
├── controllers/             # um por domínio
├── services/                # opcional: regra reutilizável
├── middlewares/             # tratamento de erros, auth, logging
├── <acesso-a-banco>         # criação de conexão/sessão, sem estado global mutável
└── <entry-point>            # composition root
```

## Adaptando à stack (a partir do Stack Profile)

1. **Nomes e localização**: use as pastas/módulos/pacotes idiomáticos da stack e a convenção de nomes dela. Se a stack organiza por **domínio/feature** em vez de por camada técnica, mantenha as **responsabilidades** separadas dentro de cada módulo de domínio.
2. **Vocabulário**: se a comunidade da stack não usa "MVC" (usa, por exemplo, handlers/services/repositories, ou portas e adaptadores), **preserve as responsabilidades do MVC com o vocabulário idiomático** e declare o mapeamento no relatório: `Model → <termo>`, `Controller → <termo>`, `View/Routes → <termo>`.
3. **Mecanismos**: injeção de dependência, tratamento de erros, validação e registro de rotas seguem o mecanismo recomendado pelo framework (container, construtor, fábrica, módulos, middleware, etc.), não um inventado.
4. **Convenções de visibilidade/pacotes**: respeite regras da linguagem (ex.: o que é público/privado, ciclos de importação proibidos) para que a estrutura compile e rode.
5. **Não importe** estrutura de outra stack: o que é natural em uma pode ser anti-idiomático em outra.

## Projetos já parcialmente organizados

Não recrie o que já funciona. Verifique por camada:

| Item | Se já existe | Se falta |
|---|---|---|
| Config | Corrigir segredos hardcoded | Criar módulo de config |
| Models | Remover regra de negócio que vazou para eles e consultas inseguras | Criar |
| Routes | Retirar regra e acesso a dados das rotas | Separar de controllers |
| Services/Controllers | Manter; corrigir acoplamento e duplicação | Criar controller entre rota e service |
| Error handling | Centralizar e padronizar formato | Criar tratador central |
| Entry point | Transformar em composition root | Criar |

Proponha mudanças estruturais só onde houver violação ou lacuna real e justifique cada movimentação.

## Padrões de contrato

- **Formato de erro único**: use o formato **já adotado pela API** (preserve o contrato); se não houver, defina um (`{"error": "<mensagem>"}` ou equivalente idiomático).
- **Status coerentes**: 400 validação, 401/403 autenticação/autorização, 404 não encontrado, 409 conflito, 500 inesperado (sem detalhes internos ao cliente).
- Logging via mecanismo idiomático, não saída direta de debug.
- Segredos e portas por configuração externa; arquivo de exemplo documentado; nenhum valor real versionado.

## Checklist de aceite da estrutura

- [ ] Config extraída, sem hardcoded
- [ ] Models abstraem dados; consultas parametrizadas
- [ ] Views/Routes só roteiam
- [ ] Controllers concentram o fluxo
- [ ] Error handling centralizado
- [ ] Entry point claro; comando de execução preservado
- [ ] Dependências na direção correta (verificar no re-scan)
- [ ] Estrutura compila/roda segundo as regras da stack
