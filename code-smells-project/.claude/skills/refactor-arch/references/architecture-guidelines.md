# MVC Architecture Guidelines

## Visao Geral

O padrao MVC (Model-View-Controller) separa responsabilidades em 3 camadas:

- **Model** — Estrutura de dados, acesso ao banco, regras de dominio
- **View/Routes** — Definicao de endpoints, serializacao de respostas HTTP
- **Controller** — Orquestracao do fluxo, logica de negocio, coordenacao de services

## Estrutura de Diretorios

Organize o projeto com camadas separadas. A nomenclatura exata dos diretorios e arquivos deve seguir a convencao da stack detectada na Fase 1:

```
config/          — Modulo de configuracao (env vars, constantes)
models/          — Um modulo por dominio, responsavel por dados
controllers/     — Um modulo por dominio, responsavel por logica
routes/          — Um modulo por grupo de endpoints, responsavel por HTTP
services/        — Servicos cross-cutting (notificacao, pagamento, etc.)
middlewares/     — Error handling, auth, logging
database/        — Configuracao e inicializacao do banco
app              — Entry point (composition root)
```

**Adaptacao ao contexto:** Se o projeto ja possui parte dessa estrutura, PRESERVE o que esta adequado e REORGANIZE apenas o que precisa. Nao recrie diretorios que ja existem e funcionam.

## Responsabilidades de Cada Camada

### Model Layer
- Define schema/estrutura dos dados
- Operacoes CRUD no banco
- Validacao de campos (tipos, obrigatoriedade)
- Metodos de dominio (ex: verificacao de status, calculos derivados)
- **NUNCA** importa ou depende de objetos de request/response HTTP
- **NUNCA** contem logica de roteamento ou codigos de status HTTP

### Controller Layer
- Recebe dados validados das routes
- Aplica regras de negocio (alem de validacao de campos)
- Chama metodos dos models para operacoes de dados
- Chama services para preocupacoes transversais (notificacao, pagamento)
- Retorna dados estruturados para a route
- **NUNCA** contem queries SQL ou acesso direto ao banco
- **NUNCA** contem codigo HTTP-specific (status codes, objetos de response)

### Route/View Layer
- Define patterns de URL e metodos HTTP
- Extrai parametros do request (body, query params, path params)
- Chama o controller method apropriado
- Formata e retorna HTTP responses (status codes, corpo)
- Registra os endpoints no sistema de roteamento da stack
- **NUNCA** contem logica de negocio
- **NUNCA** contem database queries

### Config Layer
- Toda configuracao vem de variaveis de ambiente
- Strings de conexao, chaves secretas, portas, flags
- Fornece valores default apenas para desenvolvimento local
- **NUNCA** contem valores sensiveis hardcoded

### Middleware Layer
- Error handling centralizado — um ponto captura todos os erros
- Formato de resposta de erro consistente
- CORS, authentication, logging de requests

### Service Layer
- Logica que cruza multiplos dominios ou concerns
- Integracao com servicos externos (email, pagamento, notificacao)
- Pode ser chamado por controllers

### Entry Point
- Cria a instancia da aplicacao
- Carrega configuracao
- Inicializa database
- Registra routes e middlewares
- Inicia o servidor

Deve ser minimal — apenas o "composition root" que conecta os componentes.

## Principios

1. **Direcao de dependencia:** Routes → Controllers → Models. Nunca o reverso.
2. **Single Responsibility:** Cada arquivo/modulo cuida de um conceito de dominio.
3. **Sem God Classes:** Dividir arquivos multi-dominio em modulos separados.
4. **Configuracao externa:** Todos secrets e config vem de variaveis de ambiente.
5. **Error handling centralizado:** Um middleware captura erros de forma consistente.
6. **Parameterized queries:** Sempre usar placeholders, nunca concatenacao.
7. **Sem logica de negocio em Routes:** Routes apenas extraem dados e chamam controller.
8. **Sem SQL em Controllers:** Controllers chamam model methods, models executam queries.
9. **Hash seguro de senhas:** Usar biblioteca reconhecida da stack, nunca algoritmos fracos.
10. **Fluxo assincrono linear:** Preferir async/await ou equivalente da stack ao inves de nesting profundo.
