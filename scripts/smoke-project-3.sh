#!/usr/bin/env bash
# Smoke test do projeto 3 (task-manager-api). Assume banco recém-semeado por seed.py.
# Uso: smoke-p3.sh <dir-de-saida>
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
  printf '%-26s %-6s %-38s -> %s\n' "$nome" "$metodo" "$caminho" "$code"
}

# --- infra ---
req index           GET  /
req health          GET  /health

# --- tasks (leitura) ---
req tasks_list      GET  /tasks
req task_get        GET  /tasks/1
req task_404        GET  /tasks/999999
req tasks_search    GET  "/tasks/search?q=bug"
req tasks_filtro    GET  "/tasks/search?status=pending&priority=1"
req tasks_stats     GET  /tasks/stats

# --- tasks (escrita) ---
req task_create     POST /tasks '{"title":"Task de smoke test","description":"criada pelo smoke","status":"pending","priority":2,"user_id":1,"category_id":1,"due_date":"2026-12-31","tags":["smoke","test"]}'
req task_400_vazio  POST /tasks '{}'
req task_400_titulo POST /tasks '{"title":"ab"}'
req task_400_status POST /tasks '{"title":"Titulo valido","status":"inexistente"}'
req task_404_user   POST /tasks '{"title":"Titulo valido","user_id":999999}'
req task_update     PUT  /tasks/11 '{"title":"Task de smoke editada","status":"in_progress","priority":1}'
req task_up_404     PUT  /tasks/999999 '{"title":"Nada"}'
req task_delete     DELETE /tasks/11
req task_del_404    DELETE /tasks/999999

# --- users ---
req users_list      GET  /users
req user_get        GET  /users/1
req user_404        GET  /users/999999
req user_tasks      GET  /users/1/tasks
req user_create     POST /users '{"name":"Smoke User","email":"smoke@teste.com","password":"senha","role":"user"}'
req user_400_email  POST /users '{"name":"X","email":"invalido","password":"senha"}'
req user_409_dup    POST /users '{"name":"Dup","email":"joao@email.com","password":"senha"}'
req user_400_vazio  POST /users '{}'
req user_update     PUT  /users/4 '{"name":"Smoke User Editado","role":"manager"}'
req user_up_404     PUT  /users/999999 '{"name":"Nada"}'
req user_delete     DELETE /users/4
req user_del_404    DELETE /users/999999

# --- auth ---
req login_ok        POST /login '{"email":"joao@email.com","password":"1234"}'
req login_401       POST /login '{"email":"joao@email.com","password":"errada"}'
req login_400       POST /login '{}'

# --- relatórios ---
req report_summary  GET  /reports/summary
req report_user     GET  /reports/user/1
req report_user_404 GET  /reports/user/999999

# --- categorias ---
req cats_list       GET  /categories
req cat_create      POST /categories '{"name":"Smoke Cat","description":"categoria de teste","color":"#123456"}'
req cat_400         POST /categories '{}'
req cat_update      PUT  /categories/5 '{"name":"Smoke Cat Editada","color":"#654321"}'
req cat_up_404      PUT  /categories/999999 '{"name":"Nada"}'
req cat_delete      DELETE /categories/5
req cat_del_404     DELETE /categories/999999
