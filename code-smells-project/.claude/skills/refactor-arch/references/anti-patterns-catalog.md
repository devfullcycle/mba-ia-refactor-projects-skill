# Catálogo de anti-patterns (Fase 2)

Descrito por **princípio e sinal conceitual**, sem sintaxe de linguagem. Cada entrada: sinais de detecção acionáveis, severidade e o padrão do playbook (PB-xx) que corrige. Sinais textuais específicos da stack vêm do **Stack Profile**. Confirme sempre lendo o trecho.

## Escala de severidade

| Nível | Definição |
|---|---|
| **CRITICAL** | Falhas graves de arquitetura ou segurança: impedem o funcionamento correto, expõem dados sensíveis (credenciais hardcoded, SQL Injection) ou violam por completo a separação de responsabilidades (God Class com banco, lógica e roteamento no mesmo arquivo) |
| **HIGH** | Fortes violações de MVC/SOLID que dificultam manutenção e testes: lógica de negócio pesada em Controllers, forte acoplamento sem injeção de dependência, estado global mutável |
| **MEDIUM** | Padronização, duplicação, performance moderada: N+1, middlewares usados de forma inadequada, validações ausentes, APIs deprecated |
| **LOW** | Legibilidade: nomes ruins, magic numbers, código morto, saída de debug no lugar de logger |

Em dúvida entre dois níveis, escolha o **mais alto** só se houver impacto demonstrável (dado exposto, quebra de isolamento/teste); senão o mais baixo. Explique a escolha na descrição.

---

## CRITICAL

### AP-01 God Class / God File / God Method
- **Sinais**: unidade (arquivo/classe/módulo) com 3+ responsabilidades (ver project-analysis §6); mais de ~300 linhas misturando consulta a dados, regra, validação, formatação e roteamento; atende vários domínios de negócio; função com mais de ~50 linhas e vários níveis de condicional/loop aninhados; unidade genérica ("Manager", "Utils", "Helper") que faz tudo.
- **Corrige**: PB-01.

### AP-02 Credenciais e segredos hardcoded
- **Sinais**: nomes como *secret, password, token, api key, connection string, private key* **atribuídos a literais** no código-fonte; chaves de serviços externos (pagamento, e-mail, nuvem) embutidas; arquivo de configuração com segredos reais versionado.
- **Corrige**: PB-02.

### AP-03 Injeção em consultas (SQL e similares)
- **Sinais**: consulta construída por **concatenação ou interpolação** de dados externos (parâmetro de requisição, corpo, cabeçalho); ausência de parâmetros/placeholders do driver/ORM; identificadores dinâmicos (tabela, coluna, ordenação) vindos do cliente sem lista de permissão; construção de consultas "raw" com entrada externa.
- **Corrige**: PB-03.

### AP-04 Autenticação e segurança de dados quebradas
- **Sinais**: senha guardada/comparada em texto puro ou com função de hash inadequada para senhas (rápida/sem sal); resposta que devolve senha, hash ou token; operações administrativas ou destrutivas (resetar dados, executar consulta/comando arbitrário) **sem autenticação/autorização**; execução dinâmica de código/comando com entrada externa; CORS totalmente aberto junto com credenciais.
- **Corrige**: PB-04. O que é "hash adequado" nesta stack vem do Stack Profile.

---

## HIGH

### AP-05 Lógica de negócio em Controllers/Rotas ("fat controller")
- **Sinais**: handler de rota com cálculos, regras (desconto, estoque, status), vários condicionais de domínio, acesso direto ao banco, e dezenas de linhas.
- **Corrige**: PB-05.

### AP-06 Estado global mutável e acoplamento forte sem injeção de dependência
- **Sinais**: variáveis globais/módulo-nível **mutáveis** (cache, contadores, conexão compartilhada); unidades que **criam** suas dependências internamente; dependências circulares; singletons ocultos que impedem substituir a dependência em testes.
- **Corrige**: PB-06.

### AP-07 Violação de camadas
- **Sinais**: consulta a dados dentro de rota/controller; model que conhece a requisição/resposta HTTP ou chama o controller; rota que usa o driver de banco; config acessada por todos os lados.
- **Corrige**: PB-01, PB-05.

### AP-08 Configuração insegura de produção / exposição de internals
- **Sinais**: modo debug habilitado e/ou servidor exposto em todas as interfaces por padrão; resposta que devolve pilha de execução ou mensagem interna do erro ao cliente; logs com dados sensíveis; endpoint que expõe configuração/ambiente. (Se expõe segredos reais, eleve para CRITICAL.)
- **Corrige**: PB-02, PB-07.

---

## MEDIUM

### AP-09 Consultas N+1
- **Sinais**: consulta (ou chamada a serviço/ORM que consulta) **dentro de laço** ou iteração, uma por item; carregamento tardio de relação ao percorrer uma lista.
- **Corrige**: PB-08.

### AP-10 Validação de entrada ausente ou inconsistente
- **Sinais**: dados do cliente usados sem checar presença, tipo, faixa ou formato; conversões sem tratamento de falha; regras de validação duplicadas e divergentes entre rotas.
- **Corrige**: PB-09.

### AP-11 Tratamento de erros ausente, ruidoso ou espalhado
- **Sinais**: captura genérica que **engole** o erro; resposta de erro montada manualmente em cada rota; ausência de tratador global; formatos de erro diferentes entre endpoints; status de sucesso para erro.
- **Corrige**: PB-07.

### AP-12 Código duplicado
- **Sinais**: blocos idênticos ou quase em 2+ lugares (serialização, validação, montagem de consulta, cálculo, tratamento de erro).
- **Corrige**: PB-10.

### AP-13 APIs deprecated / obsoletas
- **Como detectar** (sem tabela fixa): 
  1. Parta da lista **"Deprecated / removed APIs"** do Stack Profile, já específica da versão detectada.
  2. Procure no código **cada** uso (imports, chamadas, anotações, flags) e registre arquivo:linha.
  3. Sinais genéricos adicionais: avisos de deprecation em logs de build/execução; marcações de obsolescência na documentação do símbolo; funções cuja página oficial aponta substituto; construções que o guia de migração da versão removeu; bibliotecas descontinuadas/sem manutenção; estilo de código anterior a recursos modernos da linguagem (ex.: aninhamento de callbacks onde a linguagem já oferece alternativa assíncrona estruturada).
  4. Para cada uso informe: **obsoleto → substituto → fonte**. Sem fonte, marque "a verificar".
- **Severidade**: MEDIUM; LOW se só estético; HIGH se já foi **removido** na versão em uso e quebra o código ou a atualização.
- **Corrige**: PB-11.

---

## LOW

### AP-14 Magic numbers e strings soltas
- **Sinais**: literais numéricos ou de texto sem nome em condições, cálculos, limites, status, portas, timeouts; o mesmo literal repetido.
- **Corrige**: PB-12.

### AP-15 Nomenclatura ruim
- **Sinais**: nomes de 1-2 letras fora de laços curtos, abreviações opacas, mistura de convenções de estilo da própria stack, nomes que não dizem o que a função faz (`process`, `handle`, `doStuff`).
- **Corrige**: PB-12.

### AP-16 Código morto, comentado e logging inadequado
- **Sinais**: blocos comentados, funções/imports/variáveis nunca usados, saídas de debug diretas no console no lugar do logger, pendências esquecidas (TODO/FIXME).
- **Corrige**: PB-12.

---

## Checklist de cobertura (aplique em todo projeto)

- [ ] Segredos e configuração (AP-02, AP-08)
- [ ] Todas as consultas a dados (AP-03, AP-09)
- [ ] Autenticação, senhas e dados expostos (AP-04)
- [ ] Cada handler/rota (AP-05, AP-10, AP-11)
- [ ] Estado global e criação de dependências (AP-06)
- [ ] Tamanho e responsabilidades de cada unidade (AP-01, AP-07, AP-12)
- [ ] Uso de APIs vs. lista do Stack Profile (AP-13)
- [ ] Legibilidade (AP-14..16)
