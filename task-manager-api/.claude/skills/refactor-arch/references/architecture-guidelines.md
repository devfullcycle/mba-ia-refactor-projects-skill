# Architecture Guidelines — Alvo MVC (Fase 3)

Regras do padrão alvo. MVC aqui é adaptado para APIs: a camada "View" é o
roteamento + serialização HTTP (JSON), não telas. O objetivo é **separação de
responsabilidades**, **testabilidade** e **baixo acoplamento** (SOLID).

## Estrutura de diretórios alvo

Idioma-dependente, mas o mapeamento conceitual é sempre o mesmo. Exemplo canônico:

```
src/
├── config/        # configuração + segredos via env (settings)
├── models/        # acesso a dados + regras de domínio, por entidade
├── controllers/   # orquestração do caso de uso (fluxo da aplicação)
├── services/      # (opcional) regra de negócio reutilizável e efeitos colaterais
├── views/ ou routes/  # roteamento HTTP, (de)serialização, status codes
├── middlewares/   # error handling centralizado, auth, logging
└── app.(py|js)    # entry point enxuto = composition root
```

Em Flask: `routes/` com Blueprints para a camada de roteamento; `app.py` só
compõe. Em Express: `routes/` com `Router`, `controllers/`, `models/` (ou
`repositories/`), `middlewares/` para error handler.

## Responsabilidades por camada

### Config
- Único lugar que lê o ambiente (`os.environ` / `process.env`).
- Sem segredos literais. Fornece `.env.example` com as chaves necessárias.
- Exposta como objeto/estrutura de configuração injetável.

### Models (dados + domínio)
- Encapsulam acesso a dados (queries **parametrizadas** / ORM).
- Contêm regras de domínio que pertencem à entidade (ex.: `is_overdue`,
  cálculo de total do pedido) e a serialização canônica (`to_dict`/DTO) —
  **uma só** fonte de verdade, sem expor segredos/senhas.
- Não conhecem HTTP (nada de `request`/`res`).

### Services (quando houver regra de negócio relevante)
- Orquestram múltiplos models, transações e efeitos colaterais (e-mail, SMS,
  pagamento, relatórios).
- Recebem suas dependências por injeção (construtor/parâmetro) — sem estado
  global mutável.
- Retornam dados/erros de domínio, nunca objetos HTTP.

### Controllers (fluxo da aplicação)
- Ponto fino entre a rota e o domínio: lê input já validado, chama
  service/model, devolve resultado.
- Sem SQL, sem regra de negócio pesada, sem efeitos colaterais diretos.

### Views / Routes (HTTP)
- Declaram paths, métodos e middlewares.
- Fazem (de)serialização e escolhem status codes.
- Delegam imediatamente ao controller. Validação de input via schema/validador
  central (não `if` espalhado).

### Middlewares
- **Error handler centralizado:** captura exceções, mapeia para status/JSON
  padrão, não vaza stack trace ao cliente.
- Auth, CORS, logging estruturado.

### Entry point (composition root)
- Cria a app, carrega config, injeta dependências, registra rotas e
  middlewares, sobe o servidor. Nada de regra de negócio aqui.

## Invariantes de comportamento (não quebrar)

- **Mesmos contratos de API:** paths, métodos HTTP, formato de
  request/response e status codes idênticos aos originais.
- Mesmos nomes de campos no JSON de resposta (salvo remoção deliberada de
  segredo, ex.: parar de devolver `senha`/`secret_key` — isso é correção, não
  regressão; registre no relatório).
- Comportamento observável preservado para cada endpoint mapeado na Fase 1.

## Adaptação ao ponto de partida

- **Monolito desestruturado** (ex.: tudo em `models.py`+`controllers.py` com
  SQL cru): crie a árvore MVC completa, quebre por entidade, parametrize
  queries, extraia config e error handler.
- **Camadas parciais** (ex.: já tem `models/`, `routes/`, `services/`, `utils/`):
  **preserve o que é bom**. Foque em: extrair regra de negócio das rotas para
  services, centralizar validação/serialização (remover duplicação), corrigir
  segurança (hash de senha, segredos em env), adicionar camada de
  controller/service onde a rota faz trabalho demais, mover regra de domínio
  que está em `utils/`. Não reescreva arquivos saudáveis só para "parecer novo".

## Definition of Done

- [ ] Diretórios por camada conforme acima.
- [ ] Config isolada, sem segredos hardcoded; `.env.example` presente.
- [ ] Models abstraem dados e serialização; queries parametrizadas/ORM.
- [ ] Views/Routes separadas e finas.
- [ ] Controllers/services concentram o fluxo; sem regra de negócio na rota.
- [ ] Error handling centralizado.
- [ ] Entry point = composition root enxuto.
- [ ] App inicia sem erros e todos os endpoints originais respondem.
