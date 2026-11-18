# Guidelines de Arquitetura — MVC Alvo

Princípio: separar **o que o sistema sabe** (dados e regras), **como fala com o mundo** (HTTP/Views) e **quem coordena** (Controllers). Adapte nomes de pastas ao idioma da stack, mantendo as responsabilidades.

## Camadas e responsabilidades

### Models (dados e regras de domínio)
- **Faz**: define entidades, acessa o banco (queries parametrizadas ou ORM), aplica regras de negócio e invariantes (cálculos, estados válidos), converte linha ↔ objeto.
- **Não faz**: conhece `request`/`response`, status HTTP, JSON de resposta, templates.
- Se a regra de negócio crescer, extraia **Services** (módulo de serviço chamado pelo controller) — opcional, mas preferível a inflar o controller.

### Views / Routes (apresentação e roteamento)
- **Routes**: mapeia método + caminho → função do controller. Só isso. Pode aplicar middlewares (auth, validação de schema).
- **Views**: forma da resposta — templates (apps server-rendered) ou serializers/DTOs/formatadores JSON em APIs. Decide *como* o dado é apresentado (campos expostos, omitir senha, formato de datas).
- **Não faz**: SQL, regra de negócio.

### Controllers (orquestração)
- **Faz**: extrai e valida dados do request, chama Model/Service, escolhe o status HTTP, devolve a resposta via View/serializer, delega erros ao tratador central.
- **Não faz**: SQL, cálculos de negócio, formatação detalhada, leitura de variáveis de ambiente.

### Complementares
- **Config**: único local que lê env vars/segredos e expõe configuração tipada (porta, DB URL, flags).
- **Middlewares / Error handler**: autenticação, logging, tratamento centralizado de exceções com formato de erro uniforme (`{ "error": "...", "code": ... }`).
- **Composition root (entry point)**: cria app, registra rotas e middlewares, injeta conexão/config, inicia servidor. Deve ter poucas linhas e nenhuma regra.
- **Database layer**: criação da conexão/pool e inicialização de schema/seed isoladas, sem estado global solto.

## Regras de dependência

```
Routes → Controllers → Models/Services → Database
              ↓
           Views/Serializers
```

- Dependências apontam **para dentro**; Models nunca importam Controllers/Routes.
- Controller nunca fala SQL; Route nunca contém lógica.
- Config é injetada/importada, nunca duplicada.
- Cada arquivo tem uma razão para mudar (SRP); alvo prático: < ~200 linhas por arquivo.

## Estrutura alvo (adapte à stack)

```
project/
├── app / main / server          # entry point (composition root)
├── config/                      # settings, env
├── models/                      # entidades + acesso a dados (+ services/)
├── controllers/                 # orquestração por recurso
├── routes/  (ou views/)         # roteamento; views/serializers/templates
├── middlewares/                 # auth, erros, logging
└── database/                    # conexão, schema, seeds
```

Exemplos de tradução: Flask → `blueprints` em `routes/`, `models/`, `controllers/`; Express → `routes/`, `controllers/`, `models/`, `middlewares/`; Django → já impõe `models.py`/`views.py`/`urls.py` (mova regra de views para `services.py`/models); Spring → `controller`/`service`/`repository`/`model` packages; Laravel → já MVC (foque em controllers gordos e queries em controllers).

## Projetos já em camadas

Não recrie a estrutura. Corrija apenas os desvios: lógica em controller, SQL fora de model, config espalhada, deprecated, segurança, duplicação.

## Checklist de conformidade (use para validar a Fase 3)

- [ ] Entry point só compõe e inicia
- [ ] Nenhum SQL/ORM em controllers ou rotas
- [ ] Nenhuma regra de negócio em rotas/controllers
- [ ] Segredos vêm de config/env
- [ ] Erros tratados em um lugar, formato uniforme
- [ ] Respostas passam por serializer/view (sem vazar campos sensíveis)
- [ ] Contratos públicos (URLs, métodos, formato) preservados
