# Guidelines de Arquitetura MVC (Fase 3)

Alvo da refatoração: separação clara de responsabilidades no padrão MVC (adaptado para APIs backend, onde "View" é a camada de rotas/serialização de resposta). A skill é agnóstica de tecnologia — os nomes de pasta abaixo são convenção; adapte a idiomática da linguagem, mas **respeite as responsabilidades de cada camada**.

## Estrutura alvo

```
src/ (ou raiz, conforme convenção da stack)
├── config/            # configuração e leitura de variáveis de ambiente
├── models/            # entidades + acesso a dados por domínio
├── controllers/       # orquestração do fluxo de cada caso de uso
├── views/ ou routes/  # definição de rotas e serialização de resposta
├── services/          # regras de negócio reutilizáveis (quando fizer sentido)
├── middlewares/       # transversais: erro, auth, logging
└── app entry point    # composition root: monta e conecta tudo
```

Nem todo projeto precisa de todas as pastas — crie as camadas que o domínio exige. O mínimo é: **config, models, controllers, routes/views, entry point e tratamento de erro centralizado.**

## Responsabilidades por camada

### Config
- Ler variáveis de ambiente (segredos, string de conexão, porta, flags).
- Fornecer defaults seguros para desenvolvimento.
- **Nunca** conter segredos hardcoded. Não conter lógica de negócio.

### Models
- Representar entidades do domínio.
- Encapsular **todo** o acesso a dados (queries parametrizadas ou ORM).
- Métodos de domínio da entidade (ex.: `is_overdue()`, `check_password()`).
- **Não** conhecer request/response HTTP.

### Controllers
- Um handler por caso de uso.
- Fluxo: receber dados já validados → chamar model/service → devolver resultado ao roteador.
- **Não** conter SQL nem regra de negócio complexa; **não** montar resposta HTTP diretamente com detalhes de framework além do necessário.

### Views / Routes
- Declarar rotas, métodos HTTP e mapeá-los para controllers.
- Serialização da resposta e códigos de status.
- Aplicar middlewares (auth, validação) na entrada.
- **Não** conter lógica de negócio nem acesso a dados.

### Services (opcional, quando há regra reutilizável)
- Regras de negócio que atravessam múltiplos controllers ou models.
- Recebem dependências por injeção (testáveis em isolamento).

### Middlewares
- Tratamento de erro **centralizado** (um único ponto que formata respostas de erro).
- Autenticação/autorização.
- Logging estruturado.

## Princípios (SOLID aplicado)

- **SRP:** cada arquivo/classe tem uma responsabilidade. Se um arquivo faz banco + rota + negócio, está errado.
- **DIP:** dependências (banco, serviços) injetadas, não instanciadas internamente. Facilita teste.
- **DRY:** validação e lógica repetida vão para um único lugar reutilizável.
- **Sem estado global mutável:** estado encapsulado, escopo por requisição.

## Invariantes de comportamento (não quebrar)

Ao refatorar, **preserve o contrato externo**:
- Mesmas rotas (paths), mesmos métodos HTTP.
- Mesmos formatos de request e response (chaves do JSON, estrutura).
- Mesmos códigos de status.
- Mesmo idioma de mensagens e nomenclatura de domínio.

A refatoração é interna: quem consome a API não deve perceber diferença, exceto correções de segurança inevitáveis (ex.: senha deixa de ser retornada, endpoint perigoso é removido/protegido — documentar essas mudanças no resumo final).

## Estratégia por perfil de projeto

- **Monolito/desestruturado:** criar a estrutura MVC completa do zero, migrando o código existente para as camadas.
- **God Class:** quebrar a classe em config + models + controllers + routes; extrair seed para script separado.
- **Parcialmente organizado:** preservar as camadas já corretas; corrigir apenas vazamentos (mover negócio das rotas para services/models, eliminar duplicação, centralizar erro). **Não reescrever o que já está adequado.**
