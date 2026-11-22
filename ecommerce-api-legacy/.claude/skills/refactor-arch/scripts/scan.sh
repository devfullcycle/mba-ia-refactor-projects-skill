#!/usr/bin/env bash
# scan.sh: inventário e candidatos a anti-patterns (HEURÍSTICO, não é gate), neutro de linguagem.
# Uso: bash scan.sh [diretório] [arquivo-de-padrões-extra]
#   Padrões extra: uma linha por padrão no formato "ID ::: regex-ERE" ('#' = comentário).
#   Gere-o a partir do Stack Profile, FORA do projeto (diretório temporário).
# Saída: seções "== X ==" e linhas "AP-XX|arquivo:linha|trecho". Sempre sai com 0.
set -u
ROOT="${1:-.}"
EXTRA="${2:-}"
cd "$ROOT" || { echo "ERRO: diretório inválido: $ROOT"; exit 0; }

# Diretórios de dependências instaladas, saídas de build, caches e metadados (qualquer ecossistema).
EXCL_DIRS=(node_modules .git venv .venv env __pycache__ dist build out target vendor bin obj .gradle .idea .vscode coverage .next .cache .claude reports)
# Arquivos que não são código-fonte (documentação, dados, mídia, lock, configuração declarativa).
NON_SRC='\.(md|txt|json|ya?ml|toml|lock|xml|svg|png|jpe?g|gif|ico|webp|woff2?|ttf|eot|csv|db|sqlite3?|log|map|zip|gz|tar|pdf|http|rest|ini|cfg|conf|properties|sum|mod|env|example)$|\.min\.[a-z]+$|(^|/)(Dockerfile|Makefile|Procfile|LICENSE|README[^/]*|\.gitignore|\.env[^/]*)$'

find_src() {
  local prune=()
  for d in "${EXCL_DIRS[@]}"; do prune+=(-name "$d" -o); done
  find . \( "${prune[@]}" -false \) -prune -o -type f -print 2>/dev/null \
    | grep -vEi "$NON_SRC" | sort
}
SRC_FILES="$(find_src)"

echo "== ROOT FILES (identifique manifestos e configuração pelo papel) =="
ls -1A 2>/dev/null | grep -vE '^(node_modules|\.git)$' | head -n 60

echo "== EXTENSIONS (contagem de arquivos-fonte por extensão) =="
echo "$SRC_FILES" | sed -E 's/.*\.([A-Za-z0-9]+)$/\1/' | sort | uniq -c | sort -rn | head -n 12

echo "== SOURCE FILES (linhas arquivo) =="
total=0; count=0
while IFS= read -r f; do
  [ -z "$f" ] && continue
  n=$(wc -l < "$f" 2>/dev/null | tr -d ' '); n="${n:-0}"
  echo "$n $f"; total=$((total + n)); count=$((count + 1))
done <<< "$SRC_FILES"
echo "TOTAL files=$count lines=$total"

echo "== LARGE FILES (>300 linhas) [AP-01] =="
while IFS= read -r f; do
  [ -z "$f" ] && continue
  n=$(wc -l < "$f" 2>/dev/null | tr -d ' '); n="${n:-0}"
  [ "$n" -gt 300 ] && echo "AP-01|$f:1-$n|arquivo com $n linhas"
done <<< "$SRC_FILES"

echo "== ENTRY POINT CANDIDATES (por nome; confirme que inicia o servidor) =="
echo "$SRC_FILES" | grep -Ei '/(main|app|application|server|index|program|start|run|manage|wsgi|asgi)[^/]*$' || true

scan() { # id, regex
  local id="$1" re="$2"
  echo "$SRC_FILES" | tr '\n' '\0' | xargs -0 -r grep -HnEi -e "$re" 2>/dev/null \
    | head -n 40 | while IFS= read -r line; do
        file="${line%%:*}"; rest="${line#*:}"; ln="${rest%%:*}"; txt="${rest#*:}"
        txt="$(echo "$txt" | sed -E 's/^[[:space:]]+//' | cut -c1-110)"
        if [ "$id" = "AP-02" ]; then
          txt="$(echo "$txt" | sed -E "s/([:=][[:space:]]*[\"'\`])([^\"'\`]{0,4})[^\"'\`]*/\1\2****/")"
        fi
        echo "$id|$file:$ln|$txt"
      done
}

run_patterns() { # lê linhas "ID ::: regex" do stdin
  local line id re
  while IFS= read -r line; do
    case "$line" in ''|\#*) continue ;; esac
    id="${line%% ::: *}"; re="${line#* ::: }"
    [ "$id" = "$line" ] && continue
    scan "$id" "$re"
  done
}

echo "== CANDIDATES (padrões neutros embutidos) =="
run_patterns <<'EOF'
AP-02 ::: (secret|password|passwd|pwd|senha|token|api_?key|private_?key|credential)[A-Za-z0-9_]*[]"'[]*[[:space:]]*(:=|=|:)[[:space:]]*["'`][^"'`]{4,}["'`]
AP-03 ::: (select|insert +into|update|delete +from)[^;]{0,100}(["'`] *(\+|\.|&|\|\|)|(\+|&) *["'`]|\$\{|#\{|%s|%\(|\.format\(|[Ss]printf|String\.format|\bf["'])
AP-04 ::: \b(md5|sha-?1)\b|\beval\b|\bexec(ute)?\(|\bsystem\(|popen|reset[-_]?db|/admin/(query|sql)
AP-08 ::: debug *(=|:) *(true|1|on)\b|print_?stack|stack_?trace|traceback
AP-11 ::: (catch|except|rescue).{0,40}(\{ *\}|: *pass\b)
AP-14 ::: (==|!=|>=|<=|<|>|\*|/|%) *[0-9]+(\.[0-9]+)? *(\)|:|\{|then|&&|\|\||\band\b|\bor\b|$)
AP-16 ::: \b(TODO|FIXME|HACK|XXX)\b
EOF

if [ -n "$EXTRA" ] && [ -f "$EXTRA" ]; then
  echo "== CANDIDATES (padrões extras do Stack Profile: $EXTRA) =="
  run_patterns < "$EXTRA"
elif [ -n "$EXTRA" ]; then
  echo "AVISO: arquivo de padrões extras não encontrado: $EXTRA"
fi

echo "== NOTE =="
echo "Candidatos são pistas neutras de linguagem; confirme lendo o trecho. Sem heurística automática para AP-05/06/07/09/10/12/13/15: avalie lendo o código e usando o Stack Profile."
exit 0
