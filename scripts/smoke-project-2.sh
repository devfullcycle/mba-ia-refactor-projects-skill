#!/usr/bin/env bash
# Smoke test do projeto 2 (ecommerce-api-legacy). Banco :memory: reseta a cada boot.
# Uso: smoke-p2.sh <dir-de-saida>
set -u
BASE=${BASE:-http://localhost:3000}
OUT=$1
mkdir -p "$OUT"

req() { # req <nome> <metodo> <caminho> [json]
  local nome=$1 metodo=$2 caminho=$3 corpo=${4:-}
  local code
  if [ -n "$corpo" ]; then
    code=$(curl -s -o "$OUT/$nome.body" -w "%{http_code}" -X "$metodo" "$BASE$caminho" \
           -H 'Content-Type: application/json' -d "$corpo")
  else
    code=$(curl -s -o "$OUT/$nome.body" -w "%{http_code}" -X "$metodo" "$BASE$caminho")
  fi
  echo "$code" > "$OUT/$nome.status"
  printf '%-28s %-6s %-32s -> %s\n' "$nome" "$metodo" "$caminho" "$code"
}

# checkout — usuário novo, cartão aprovado (prefixo 4)
req checkout_novo      POST /api/checkout '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'
# checkout — usuário existente do seed
req checkout_existente POST /api/checkout '{"usr":"Leonan","eml":"leonan@fullcycle.com.br","pwd":"123","c_id":1,"card":"4555666677778888"}'
# checkout — pagamento recusado (prefixo != 4)
req checkout_recusado  POST /api/checkout '{"usr":"João","eml":"joao@teste.com","pwd":"123","c_id":1,"card":"5111222233334444"}'
# checkout — payload incompleto
req checkout_400       POST /api/checkout '{}'
# checkout — curso inexistente
req checkout_404       POST /api/checkout '{"usr":"X","eml":"x@y.com","pwd":"1","c_id":999,"card":"4111222233334444"}'

req relatorio          GET  /api/admin/financial-report

# deleção destrutiva (deixa órfãos no legado) — penúltimo
req user_delete        DELETE /api/users/1
# relatório após deleção: evidencia integridade referencial
req relatorio_pos_del  GET  /api/admin/financial-report
