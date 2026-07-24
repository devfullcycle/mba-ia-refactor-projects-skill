#!/usr/bin/env bash
# Smoke test do projeto 1 (code-smells-project).
# Uso: smoke-p1.sh <dir-de-saida>
# Sequência fixa e determinística; assume banco recém-criado (seed padrão).
set -u
BASE=${BASE:-http://localhost:5000}
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
  printf '%-28s %-6s %-34s -> %s\n' "$nome" "$metodo" "$caminho" "$code"
}

# --- leitura ---
req index            GET  /
req health           GET  /health
req produtos_list    GET  /produtos
req produto_get      GET  /produtos/1
req produto_404      GET  /produtos/999999
req produto_busca    GET  "/produtos/busca?q=notebook"
req produto_filtro   GET  "/produtos/busca?categoria=informatica&preco_min=100&preco_max=2000"

# --- escrita de produtos ---
req produto_create   POST /produtos '{"nome":"Produto Smoke","descricao":"teste","preco":10.5,"estoque":3,"categoria":"geral"}'
req produto_400_vazio POST /produtos '{}'
req produto_400_cat  POST /produtos '{"nome":"X Y","preco":1,"estoque":1,"categoria":"invalida"}'
req produto_update   PUT  /produtos/11 '{"nome":"Produto Smoke Editado","preco":12.0,"estoque":5,"categoria":"geral"}'
req produto_up_404   PUT  /produtos/999999 '{"nome":"Nada","preco":1,"estoque":1}'
req produto_delete   DELETE /produtos/11
req produto_del_404  DELETE /produtos/999999

# --- usuários e login ---
req usuarios_list    GET  /usuarios
req usuario_get      GET  /usuarios/1
req usuario_404      GET  /usuarios/999999
req usuario_create   POST /usuarios '{"nome":"Smoke User","email":"smoke@teste.com","senha":"segredo123"}'
req usuario_400      POST /usuarios '{}'
req login_ok         POST /login '{"email":"admin@loja.com","senha":"admin123"}'
req login_401        POST /login '{"email":"admin@loja.com","senha":"errada"}'
# sonda de segurança: SQL Injection no login (baseline = 200 vulnerável, esperado 401 após refatoração)
req login_sqli       POST /login '{"email":"x'"'"' OR '"'"'1'"'"'='"'"'1","senha":"x'"'"' OR '"'"'1'"'"'='"'"'1"}'

# --- pedidos ---
req pedido_create    POST /pedidos '{"usuario_id":1,"itens":[{"produto_id":1,"quantidade":1},{"produto_id":2,"quantidade":2}]}'
req pedido_400_vazio POST /pedidos '{}'
req pedido_400_estoq POST /pedidos '{"usuario_id":1,"itens":[{"produto_id":1,"quantidade":99999}]}'
req pedidos_list     GET  /pedidos
req pedidos_usuario  GET  /pedidos/usuario/1
req pedido_status    PUT  /pedidos/1/status '{"status":"aprovado"}'
req pedido_status_400 PUT /pedidos/1/status '{"status":"invalido"}'
req relatorio        GET  /relatorios/vendas

# --- endpoints administrativos (backdoors: devem desaparecer após refatoração) ---
req admin_query      POST /admin/query '{"sql":"SELECT COUNT(*) as c FROM produtos"}'
req admin_reset      POST /admin/reset-db
req produtos_pos_reset GET /produtos
