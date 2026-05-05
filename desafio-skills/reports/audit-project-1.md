# Relatório de auditoria — Projeto 1 (`code-smells-project`)

**Stack detectada:** Python 3.x + Flask 3.1.x + SQLite (`loja.db`)  
**Domínio:** API de e-commerce (produtos, usuários, pedidos, relatório de vendas)  
**Arquitetura (pré-refatoração):** monólito em poucos arquivos; SQL e regras concentrados em `models.py`; rotas em `app.py` + `controllers.py`.

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed (pré-refatoração)

## Summary
CRITICAL: 3 | HIGH: 2 | MEDIUM: 2 | LOW: 1

## Findings

### [CRITICAL] SQL injection por concatenação de strings em queries
File: models.py:24-31, 47-50, 68-69, 110-111, 127-128, 140-166, 279-281, 289-297 (legado; arquivo removido na Fase 3)
Description: Uso de concatenação de valores de entrada em SQL (`execute("... " + ...)`), incluindo login e busca.
Impact: Comprometimento total do banco de dados; explorável remotamente.
Recommendation: Substituir por consultas parametrizadas (`?` + tupla de parâmetros).

### [CRITICAL] Endpoint administrativo executando SQL arbitrário
File: app.py:59-78 (legado)
Description: Rota `/admin/query` aceitava SQL do cliente e executava no SQLite.
Impact: Backdoor com impacto equivalente a acesso root ao banco.
Recommendation: Remover rota ou substituir por ferramenta operacional autenticada fora da API pública.

### [CRITICAL] Segredo e modo debug expostos / hardcoded
File: app.py:7-8; controllers.py:264-290 (legado)
Description: `SECRET_KEY` fixa, `DEBUG=True`, e health retornando `secret_key` no JSON.
Impact: Sessões/forgery e vazamento de configuração sensível.
Recommendation: Variáveis de ambiente; health sem campos secretos.

### [HIGH] God module de persistência e regras
File: models.py (legado)
Description: Arquivo único concentra SQL, regras de pedido e formatação de relatórios.
Impact: Baixa coesão; difícil testar e evoluir por domínio.
Recommendation: Repositórios por agregado (produtos, usuários, pedidos) + serviços/controllers.

### [HIGH] Exposição de senhas de usuários em listagens
File: models.py:72-87 `get_todos_usuarios` (legado)
Description: Resposta incluía campo `senha` em texto claro.
Impact: Violação de privacidade e amplificação de danos em vazamentos.
Recommendation: Nunca serializar credenciais; DTOs públicos sem `senha`.

### [MEDIUM] Validação e efeitos colaterais misturados à camada HTTP
File: controllers.py:24-62, 188-216 (legado)
Description: Validação extensa e `print` simulando notificações dentro de handlers HTTP.
Impact: Duplicação e acoplamento; ruído operacional.
Recommendation: Extrair validadores/casos de uso; fila ou serviço de notificação.

### [MEDIUM] APIs obsoletas / práticas legadas (verificação)
File: N/A (código legado)
Description: Não encontrado uso explícito de APIs Node/Express deprecadas; em Python, padrão `datetime.utcnow()` ainda presente em módulos legados relacionados a datas (risco de timezone naive).
Impact: Bugs subtis de timezone e manutenção.
Recommendation: `datetime.now(timezone.utc)` onde aplicável após refatoração.

### [LOW] Magic numbers em relatório de vendas
File: models.py:256-262 (legado)
Description: Faixas de faturamento e percentuais embutidos sem constantes nomeadas.
Impact: Legibilidade e risco de erro ao alterar regra comercial.
Recommendation: Constantes em `config` ou módulo de regras de negócio.

================================
Total: 8 findings
================================
```

**Nota:** Após a Fase 3, a estrutura foi reorganizada em `src/` (config, repositories, views, middleware) e o endpoint inseguro `/admin/query` foi **removido**. Reset de banco exige `ENABLE_ADMIN_RESET=true`.
