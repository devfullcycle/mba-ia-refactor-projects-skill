# Protocolo de Validação (Fase 3)

Objetivo: provar com evidência que a aplicação **sobe** e que os endpoints continuam
respondendo como antes. Sem baseline não existe validação — só esperança.

## Passo 0 — Baseline (antes de modificar qualquer arquivo)

1. **Instale as dependências** conforme a stack detectada:

```bash
# Python
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
# Node
npm install
# outras: mvn -q package -DskipTests | go build ./... | composer install
```

Se o manifesto exigir runtime mais novo que o disponível (ex.: `flask==3.1.1` requer Python
≥3.9), resolva o runtime — **não** relaxe a versão pinada do projeto sem registrar isso.

2. **Suba a aplicação em background**, capturando o log de boot:

```bash
(.venv/bin/python app.py > /tmp/baseline-boot.log 2>&1 &) ; sleep 3
# Node: (npm start > /tmp/baseline-boot.log 2>&1 &) ; sleep 3
```

3. **Exercite todos os endpoints** inventariados na Fase 1, salvando status + corpo:

```bash
BASE=http://localhost:5000
OUT=/tmp/baseline
mkdir -p $OUT

req() {  # req <nome> <método> <caminho> [json]
  local nome=$1 metodo=$2 caminho=$3 corpo=$4
  if [ -n "$corpo" ]; then
    curl -s -o "$OUT/$nome.body" -w "%{http_code}" -X "$metodo" "$BASE$caminho" \
         -H 'Content-Type: application/json' -d "$corpo" > "$OUT/$nome.status"
  else
    curl -s -o "$OUT/$nome.body" -w "%{http_code}" -X "$metodo" "$BASE$caminho" > "$OUT/$nome.status"
  fi
  echo "$metodo $caminho -> $(cat "$OUT/$nome.status")"
}

req health      GET  /health
req list        GET  /produtos
req detail      GET  /produtos/1
req create      POST /produtos '{"nome":"Teste","preco":10.5,"estoque":3}'
req not_found   GET  /produtos/999999
req bad_request POST /produtos '{}'
```

Cubra, para cada recurso: caminho felizes (list, detail, create, update, delete), **um 404** e
**um 400**. Códigos de erro fazem parte do contrato e são onde a refatoração mais quebra.

4. **Derrube o servidor** e registre o resultado do baseline (endpoint → status → resumo do corpo).

```bash
pkill -f "python app.py" || pkill -f "node src/app.js"
```

**Se a aplicação não sobe nem antes da refatoração:** registre o erro, não invente baseline.
Valide então por (a) boot limpo depois e (b) import/compilação dos módulos, e diga isso
explicitamente no relatório final.

**Efeitos colaterais:** endpoints de escrita mudam o estado do banco. Faça uma cópia do arquivo
de banco antes (`cp loja.db /tmp/baseline.db`) para comparar de forma justa, ou use os mesmos
dados de seed nas duas execuções. Banco `:memory:` reseta a cada boot — nesse caso os dois lados
já partem do mesmo estado.

## Passo 3 — Validação pós-refatoração

1. **Boot limpo** — mesma stack, novo entry point:

```bash
.venv/bin/python run.py > /tmp/after-boot.log 2>&1 &  sleep 3
grep -iE "error|traceback|exception|deprecat" /tmp/after-boot.log   # esperado: vazio
```

2. **Reexecute exatamente as mesmas chamadas** do baseline, gravando em `/tmp/after`.

3. **Compare status e forma do corpo:**

```bash
for f in /tmp/baseline/*.status; do
  n=$(basename "$f" .status)
  b=$(cat "$f"); a=$(cat "/tmp/after/$n.status" 2>/dev/null)
  [ "$b" = "$a" ] && echo "✓ $n ($b)" || echo "✗ $n: baseline=$b after=$a"
done
# diferenças de payload (ignore campos naturalmente variáveis: id, timestamp, token)
for f in /tmp/baseline/*.body; do
  n=$(basename "$f" .body)
  diff <(python3 -m json.tool "$f" 2>/dev/null) <(python3 -m json.tool "/tmp/after/$n.body" 2>/dev/null) \
    > /dev/null || echo "≠ payload: $n"
done
```

**O que conta como igual:** mesmo status, mesmas chaves, mesmos tipos. `id`, timestamps,
ordenação de lista e token podem variar. **O que conta como regressão:** status diferente,
chave que desapareceu (fora de remoção de campo sensível declarada), 500 novo, ou endpoint que
sumiu sem estar no relatório.

4. **Diferença intencional** (endpoint removido por segurança, campo sensível retirado do
   payload) não é regressão — mas tem que estar declarada no relatório final, com o finding que
   a motivou.

## Checagens estruturais (complementam o teste funcional)

```bash
# nenhum segredo literal restante
grep -rniE "(secret|password|api_?key|token)[[:space:]]*[:=][[:space:]]*['\"][^'\"]{3,}" src/ \
  | grep -vE "os\.environ|process\.env|getenv|\.env\.example"        # esperado: vazio

# nenhuma query fora da camada de dados
grep -rlE "SELECT |INSERT |UPDATE |DELETE FROM" src/ | grep -v "src/\(models\|database\)/"   # vazio

# nenhum framework HTTP importado nos models
grep -rn "from flask import\|require('express')\|res\.\|jsonify" src/models/                 # vazio

# nenhum print/console.log de diagnóstico
grep -rnE "^[[:space:]]*(print\(|console\.log\()" src/                                       # vazio

# imports circulares / boot por import
python3 -c "import importlib; importlib.import_module('src.app')"   # não deve executar I/O
```

## Rollback

Trabalhe sempre em branch, com commit do estado original antes da Fase 3. Se a validação falhar
e não for corrigível:

```bash
git status                 # confira o que mudou
git stash                  # ou: git checkout -- <arquivo>
git reset --hard HEAD      # último recurso, só com commit do baseline garantido
```

Nunca deixe o projeto em estado intermediário quebrado: ou a validação passa, ou você reverte e
reporta o motivo.

## Saída de validação

Reporte só o que executou de fato, com o número real:

```
Validation
  ✓ Application boots without errors        (/tmp/after-boot.log limpo)
  ✓ 19/19 endpoints respond as before       (status idênticos ao baseline)
  ✓ No hardcoded secrets remaining          (grep vazio em src/)
  ✓ Layer boundaries respected              (sem SQL fora de models/, sem HTTP em models/)
  ! 2 endpoints intencionalmente removidos  (POST /admin/query, POST /admin/reset-db — findings 2 e 6)
```
