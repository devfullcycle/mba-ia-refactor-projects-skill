---
name: refactor-arch
description: Auditar qualquer codebase, inclusive monorepos e sistemas poliglotas, detectar unidades executáveis, stack, arquitetura, anti-patterns e APIs deprecated, persistir o relatório na raiz do repositório antes do checkpoint humano e, somente após aprovação explícita, refatorar para MVC ou papéis arquiteturais equivalentes preservando contratos e validando cada unidade. Usar em código legado ou parcialmente organizado de qualquer linguagem, framework, runtime, domínio ou ferramenta de desenvolvimento.
---

# Refactor Arch

Executar três fases sequenciais: analisar, auditar e, após um checkpoint humano obrigatório, refatorar. Descobrir comandos e convenções a partir dos artefatos locais; não pressupor linguagem, framework, runtime, gerenciador de dependências, persistência, protocolo, controle de versão ou layout.

## Regras invariantes

1. Tratar a raiz fornecida pelo usuário, ou o diretório atual, como limite de escopo. Descobrir cada módulo, serviço, aplicação, pacote ou unidade executável dentro dela antes de analisar.
2. Preservar alterações preexistentes. Descobrir e excluir dependências vendorizadas, caches, artefatos de build, cobertura e dados gerados pelas convenções e metadados da própria codebase, não por uma lista fixa de tecnologias.
3. Manter as Fases 1 e 2 somente-leitura para a codebase. Não editar código, configuração ou documentação do projeto, formatar, instalar, migrar, iniciar serviços nem executar comandos que possam criar caches, bancos, logs ou lockfiles. Permitir somente a criação ou atualização do relatório final ao concluir a Fase 2.
4. Exibir o relatório completo ao fim da Fase 2, persistir exatamente o mesmo conteúdo no caminho final e somente então apresentar o checkpoint. Salvar o relatório não autoriza nenhuma outra modificação.
5. Não aceitar aprovação antecipada no pedido que inicia as Fases 1 e 2, silêncio ou resposta ambígua. Aceitar, em uma nova conversa, autorização explícita para a Fase 3 quando ela identificar um relatório de checkpoint persistido; nesse caso, reconstruir o ledger a partir do relatório e verificar que a codebase auditada não mudou.
6. Preservar contratos públicos observados: HTTP/RPC, comandos CLI, mensagens/eventos, jobs, interfaces de biblioteca, formatos de arquivo, UI e efeitos persistentes. Para HTTP, preservar método, caminho, status e forma essencial do payload, exceto mudança aprovada pelo usuário.
7. Não inventar findings para cumprir mínimos. Distinguir fato, inferência e incerteza e citar linhas exatas.
8. Não commitar, publicar, apagar dados nem executar operação destrutiva sem autorização explícita. Usar os recursos equivalentes disponíveis na ferramenta atual sem depender de nomes de comandos, APIs ou formatos proprietários de uma ferramenta específica.

## Resolver o caminho do relatório

Separar a raiz da codebase auditada da raiz do repositório de entrega:

1. Resolver a raiz do repositório de entrega pelos metadados do controle de versão que contém a codebase. Se não houver uma raiz inequívoca, usar a raiz de entrega fornecida pelo usuário; se ela também não existir, pedir esse caminho antes de concluir a Fase 2.
2. Persistir todos os relatórios em `<raiz-do-repositório-de-entrega>/reports/`, nunca em `<codebase>/reports/` quando a codebase for um subdiretório da raiz de entrega.
3. Neste desafio, usar obrigatoriamente este mapeamento:
   - `code-smells-project` → `reports/audit-project-1.md`;
   - `ecommerce-api-legacy` → `reports/audit-project-2.md`;
   - `task-manager-api` → `reports/audit-project-3.md`.
4. Fora deste desafio, respeitar o nome de arquivo solicitado pelo usuário ou usar `reports/audit-<codebase-name>.md`.
5. Tratar a criação do diretório `reports/` e a escrita do arquivo escolhido como a única exceção de escrita das Fases 1 e 2. Não criar um segundo diretório `reports/` dentro da codebase.

## Orquestrar com subagentes genéricos

Usar subagentes genéricos quando estiverem disponíveis e houver subtarefas independentes. Não depender de perfis nomeados ou especializados: criar agentes descartáveis com prompts específicos para o trabalho. Manter o agente principal como coordenador exclusivo da conversa, das fases, do checkpoint, da integração e da síntese.

Para cada subagente, fornecer somente:

- raiz absoluta do projeto;
- fase, objetivo e escopo exato;
- referências necessárias à tarefa;
- modo `READ_ONLY` ou lista exclusiva de arquivos autorizados para escrita;
- comandos proibidos, formato de saída e critérios de parada.

Não repassar a conversa inteira, conclusões anteriores, findings esperados nem conteúdo integral de arquivos. Mandar o agente ler os artefatos diretamente e devolver apenas evidências concisas. Não permitir que subagentes criem outros subagentes.

Manter na janela principal apenas um ledger compacto com unidades, stack, domínio, arquitetura, entry points, comandos, contratos públicos, findings verificados, plano aprovado, propriedade de arquivos e resultados de validação. Exigir de agentes de auditoria este formato:

```text
ID | severidade | anti-pattern | arquivo:linhas | evidência | impacto | recomendação | confiança
```

Encerrar os agentes de uma fase antes de iniciar a seguinte. Se subagentes não estiverem disponíveis, aplicar o mesmo protocolo sequencialmente e carregar apenas a referência da fase atual.

## Fase 1 — Analisar o projeto

Ler [project-analysis.md](references/project-analysis.md). Operar em modo somente-leitura.

Quando útil, delegar a agentes genéricos novos e independentes:

1. detectar unidades, linguagens, runtimes, frameworks, dependências, persistência, entry points e comandos prováveis;
2. mapear domínio, módulos, camadas, fluxos, interfaces públicas, testes e arquivos-fonte.

Conferir divergências diretamente nos manifests, configurações de build, entry points e registros de interface. Contar apenas arquivos-fonte efetivamente considerados e registrar inclusões e exclusões. Produzir um bloco por unidade executável e um resumo consolidado:

```text
================================
PHASE 1: PROJECT ANALYSIS
================================
Language(s):   <linguagens e evidências>
Runtime(s):    <runtimes e versões, se comprovadas>
Framework(s):  <frameworks/bibliotecas e versões, se comprovadas>
Dependencies:  <dependências arquiteturalmente relevantes>
Persistence:   <bancos, arquivos, serviços e modelos de acesso>
Domain:        <domínio inferido e evidências>
Architecture:  <estrutura atual e acoplamentos>
Entry points:  <arquivos, unidades e comandos descobertos>
Source files:  <N analisados; regra de contagem>
Contracts:     <N interfaces públicas inventariadas por tipo>
Tests:         <framework, comando ou ausência>
================================
```

Guardar no ledger o inventário de contratos no formato apropriado a cada interface. Para HTTP, incluir método, path, autenticação, entrada, status e resposta; para outras interfaces, registrar identidade, entrada, saída, erro e efeitos. Não iniciar a Fase 2 enquanto unidades, linguagens, arquitetura, domínio e contagem não estiverem sustentados por evidência.

## Fase 2 — Auditar e pedir confirmação

Ler [anti-pattern-catalog.md](references/anti-pattern-catalog.md) e [audit-report-template.md](references/audit-report-template.md). Continuar em modo somente-leitura para a codebase, mantendo como única exceção a persistência do relatório ao final da fase.

Dividir o catálogo entre agentes genéricos sem sobreposição, por exemplo:

1. segurança, configuração, MVC, SOLID e acoplamento;
2. dados, performance, validação, duplicação, erros e APIs deprecated.

Exigir evidência localizada. Confirmar cada finding no código, remover duplicatas pela causa raiz e calibrar a severidade pelo impacto concreto, nunca apenas pelo nome do padrão. Executar sempre a verificação de APIs deprecated; registrar `não encontrado` quando não houver ocorrência comprovada.

Gerar pelo menos cinco findings verificados e ao menos um `CRITICAL` ou `HIGH` quando o código oferecer evidência. Se o mínimo não for atingido, fazer uma segunda varredura de arquivos ainda não cobertos; persistindo a insuficiência, declarar o critério não atendido em vez de criar achados.

Renderizar o relatório completo conforme o template, com findings ordenados por `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` e, dentro do nível, por impacto. Incluir o plano proposto, arquivos afetados, riscos, validações, o caminho final resolvido e uma impressão digital do estado auditado suficiente para detectar mudanças posteriores, excluindo o próprio relatório.

Criar o diretório `reports/` na raiz de entrega quando necessário, persistir o relatório no caminho final antes do checkpoint e reler o arquivo para conferir conteúdo e caminho. Se a persistência ou a conferência falhar, informar o erro e não solicitar autorização para a Fase 3. Não modificar nenhum outro arquivo.

Encerrar os subagentes e, depois de salvar o relatório, terminar a resposta com exatamente este checkpoint:

```text
Phase 2 complete. Autoriza executar a Fase 3 e modificar os arquivos conforme o plano apresentado? [y/n]
```

Parar a execução e devolver o controle ao usuário. Mesmo que o pedido inicial solicite as três fases, aguardar uma resposta posterior. Se a resposta for negativa ou ambígua, manter somente o relatório já salvo e não modificar a codebase.

## Fase 3 — Refatorar e validar

Iniciar somente depois da confirmação exigida na Fase 2. Ler [mvc-guidelines.md](references/mvc-guidelines.md) e [refactoring-playbook.md](references/refactoring-playbook.md).

Permitir a retomada em uma janela de contexto nova sem repetir as Fases 1 e 2 quando o usuário identificar o relatório salvo e autorizar inequivocamente a Fase 3, por exemplo: `Autorizo a Fase 3 conforme reports/audit-project-1.md`. Nessa retomada:

1. localizar e ler o relatório inteiro antes de qualquer outra ação;
2. reconstruir do relatório a raiz auditada, contratos, findings, plano, riscos, validações e estado inicial;
3. confirmar que o relatório está no diretório `reports/` da raiz de entrega e contém um checkpoint pendente;
4. comparar a impressão digital registrada com o estado atual da codebase, ignorando o próprio relatório;
5. se o código, configuração ou contratos tiverem mudado, não aplicar um plano obsoleto: repetir as Fases 1 e 2 e atualizar o relatório antes de pedir nova aprovação.

### Preparar baseline e plano

1. Congelar o relatório já persistido e registrar a aprovação explícita recebida; não alterar os findings nem o plano aprovado.
2. Confirmar novamente o estado do controle de versão quando existir; caso contrário, comparar o inventário e os hashes dos arquivos em escopo com a impressão digital do relatório.
3. Obter um baseline reproduzível de build/load, testes, boot de cada unidade executável e contratos antes de editar. Usar ambiente, namespace, porta, storage e serviços temporários quando possível; não tocar dados reais.
4. Mapear cada finding para uma transformação do playbook e para um critério verificável.
5. Definir papéis MVC adaptados às convenções detectadas, sem impor nomes de diretórios. Em unidades sem HTTP/UI, mapear View para adapter de entrada/saída e Controller para orquestração; se MVC não for coerente, propor a separação equivalente e obter aprovação.

Se o baseline exigir credenciais ausentes, infraestrutura externa, ação destrutiva ou escolha que altere contrato público, parar e pedir orientação.

### Aplicar mudanças

Implementar em ondas pequenas:

1. configuração e infraestrutura compartilhada;
2. Models e abstração de dados;
3. Controllers e serviços de domínio;
4. Views/adapters e validação de entrada;
5. error handler central e composition root/entry point;
6. testes e documentação estritamente necessários.

Usar escrita paralela por subagentes apenas para conjuntos comprovadamente disjuntos. Manter entry point, configuração, manifesto de dependências, roteador central, error handler e relatório com um único proprietário. Informar a cada agente escritor os finding IDs, arquivos permitidos e proibidos, contratos a preservar e teste local. Proibir commits, reversões e edições fora do escopo. Inspecionar o diff após cada onda antes de liberar a próxima.

Aplicar as responsabilidades de [mvc-guidelines.md](references/mvc-guidelines.md): Models representam estado e invariantes; Controllers orquestram casos de uso; Views/adapters traduzem interfaces externas; configuração fica externa; erros têm tradução central; o bootstrap apenas compõe dependências e inicia/carrega a unidade.

### Validar de forma independente

Executar, nesta ordem:

1. análise de sintaxe, tipos ou lint disponível;
2. testes automatizados existentes e adicionados;
3. boot/load real de cada unidade aplicável, com readiness, timeout e encerramento limpo;
4. smoke/contract tests de todas as interfaces públicas do baseline; para HTTP, incluir método, path, status e forma essencial do payload;
5. nova auditoria dirigida aos findings e a regressões `CRITICAL`/`HIGH`;
6. inspeção do diff pelo controle de versão disponível ou comparação de hashes/inventários para confirmar escopo.

Preferir um subagente genérico novo para a validação final. Fornecer somente baseline, comandos e contratos; não informar o resultado esperado da revisão. Executar sequencialmente validações que compartilhem porta ou banco.

Fazer no máximo duas rodadas de correção orientadas por evidência. Se build/load, boot, testes ou contratos continuarem falhando, encerrar como incompleto, mostrar comandos e erros relevantes, não commitar e não afirmar sucesso. Não declarar `zero anti-patterns` sem varredura que o sustente; listar resíduos conhecidos.

Concluir somente quando os papéis MVC ou equivalentes estiverem coerentes, configuração e error handling estiverem centralizados, cada bootstrap estiver claro, as unidades carregarem/iniciarem sem erros e todos os contratos públicos originais permanecerem compatíveis. Informar estrutura final, arquivos alterados, validações com resultado, findings resolvidos e riscos restantes.

## Referências por fase

- Fase 1: [project-analysis.md](references/project-analysis.md)
- Fase 2: [anti-pattern-catalog.md](references/anti-pattern-catalog.md) e [audit-report-template.md](references/audit-report-template.md)
- Fase 3: [mvc-guidelines.md](references/mvc-guidelines.md) e [refactoring-playbook.md](references/refactoring-playbook.md)
