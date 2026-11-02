#!/usr/bin/env bash
# Flujo actor QA: 2 sellers + 2 buyers contra el backend local.
# No imprime tokens ni contraseñas. No borra la DB.
#
#   export QA_PASSWORD='…'
#   ./scripts/qa-api.sh
#
set -euo pipefail

BASE="${QA_API_URL:-http://localhost:8000}"
SELLER_A_EMAIL="${SELLER_A_EMAIL:-vendedor1@mail.com}"
SELLER_B_EMAIL="${SELLER_B_EMAIL:-sonaglioni.enoc@gmail.com}"
PASSWORD="${QA_PASSWORD:?exportá QA_PASSWORD}"

fail() { echo "FAIL: $*" >&2; exit 1; }

json_get() {
  python3 -c 'import json,sys; d=json.load(sys.stdin); print(eval(sys.argv[1], {"d": d}))' "$1"
}

login() {
  local email="$1"
  local body
  body="$(curl -sS -X POST "$BASE/auth/login" \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"$email\",\"password\":$(python3 -c 'import json,os; print(json.dumps(os.environ["QA_PASSWORD"]))')}")"
  python3 -c 'import json,sys; d=json.load(sys.stdin); assert d.get("access_token"), d; print(d["access_token"])' <<<"$body"
}

register_buyer() {
  local email="$1"
  local body
  body="$(curl -sS -X POST "$BASE/auth/register" \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"$email\",\"password\":$(python3 -c 'import json,os; print(json.dumps(os.environ["QA_PASSWORD"]))')}")"
  python3 -c 'import json,sys; d=json.load(sys.stdin); assert d.get("access_token"), d; print(d["access_token"])' <<<"$body"
}

auth_get() {
  local token="$1" path="$2"
  shift 2
  curl -sS -H "Authorization: Bearer $token" "$BASE$path" "$@"
}

auth_post_json() {
  local token="$1" path="$2" payload="$3"
  curl -sS -X POST -H "Authorization: Bearer $token" -H 'Content-Type: application/json' \
    -d "$payload" "$BASE$path"
}

code_of() {
  local token="$1" method="$2" path="$3"
  curl -sS -o /dev/null -w '%{http_code}' -X "$method" \
    -H "Authorization: Bearer $token" "$BASE$path"
}

health="$(curl -sS -o /dev/null -w '%{http_code}' "$BASE/health")"
[[ "$health" == "200" ]] || fail "GET /health -> $health"

export QA_PASSWORD="$PASSWORD"
token_a="$(login "$SELLER_A_EMAIL")"
token_b="$(login "$SELLER_B_EMAIL")"

store_a="$(auth_get "$token_a" '/stores' | python3 -c 'import json,sys; print(json.load(sys.stdin)["items"][0]["id"])')"
store_b="$(auth_get "$token_b" '/stores' | python3 -c 'import json,sys; print(json.load(sys.stdin)["items"][0]["id"])')"

png="$(python3 -c 'import pathlib,tempfile,sys; p=tempfile.NamedTemporaryFile(suffix=".png",delete=False); p.write(bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de0000000c49444154789c636060000000020001e221bc330000000049454e44ae426082")); print(p.name)')"

publish() {
  local token="$1" store="$2" name="$3" profit="$4"
  curl -sS -X POST -H "Authorization: Bearer $token" \
    -F "name=$name" -F quantity=6 -F price=150.00 -F "net_profit=$profit" \
    -F category=QA -F subcategory=Actores -F ships=true -F pickup=true \
    -F "image=@${png};type=image/png" \
    "$BASE/stores/$store/products" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["id"])'
}

stamp="$(date +%s)"
prod_a="$(publish "$token_a" "$store_a" "QA script A $stamp" "12.00")"
prod_hot="$(publish "$token_a" "$store_a" "QA script hot $stamp" "90.00")"
prod_b="$(publish "$token_b" "$store_b" "QA script B $stamp" "8.00")"

buyer1="qa.script.b1.${stamp}@mail.com"
buyer2="qa.script.b2.${stamp}@mail.com"
token_1="$(register_buyer "$buyer1")"
token_2="$(register_buyer "$buyer2")"

auth_get "$token_1" "/products?q=QA+script&page_size=10" >/dev/null

checkout() {
  local token="$1" product="$2" qty="$3" ful="$4" pay="$5"
  auth_post_json "$token" "/sells/checkout" \
    "{\"payment_method\":\"$pay\",\"items\":[{\"product_id\":$product,\"quantity\":$qty,\"fulfillment\":\"$ful\"}]}" \
    | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["items"][0]["id"])'
}

sell_1="$(checkout "$token_1" "$prod_a" 1 envio tarjeta)"
sell_2="$(checkout "$token_2" "$prod_b" 1 retiro efectivo)"

auth_post_json "$token_1" "/products/$prod_a/questions" '{"text":"Cuando sale el envio?"}' >/dev/null
auth_post_json "$token_2" "/products/$prod_hot/questions" '{"text":"URGENTE: hay stock de la pub cara?"}' >/dev/null
auth_post_json "$token_2" "/products/$prod_b/questions" '{"text":"Se retira hoy?"}' >/dev/null
auth_post_json "$token_1" "/sells/$sell_1/messages" '{"body":"URGENTE cambio de domicilio"}' >/dev/null
auth_post_json "$token_2" "/sells/$sell_2/messages" '{"body":"A que hora retiro?"}' >/dev/null

auth_get "$token_a" "/sells?as_seller=true&status=en_curso&from=2000-01-01" >/dev/null
auth_get "$token_a" "/sells/$sell_1" >/dev/null
auth_get "$token_a" "/sells/$sell_1/messages" >/dev/null
auth_post_json "$token_a" "/sells/$sell_1/messages" '{"body":"Despacho hoy"}' >/dev/null
auth_get "$token_b" "/sells/$sell_2" >/dev/null
auth_post_json "$token_b" "/sells/$sell_2/messages" '{"body":"Retiro de 10 a 18"}' >/dev/null

pending="$(auth_get "$token_a" "/questions?status=pending&sort=score")"
qid="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["items"][0]["id"])' <<<"$pending")"
auth_post_json "$token_a" "/questions/$qid/answers" '{"text":"Stock confirmado"}' >/dev/null

auth_get "$token_a" "/notifications" >/dev/null
auth_get "$token_a" "/dashboard" >/dev/null
auth_get "$token_b" "/dashboard" >/dev/null

anon="$(curl -sS -o /dev/null -w '%{http_code}' "$BASE/sells")"
[[ "$anon" == "401" ]] || fail "GET /sells anon -> $anon"

xss="$(curl -sS -o /dev/null -w '%{http_code}' -X POST \
  -H "Authorization: Bearer $token_1" -H 'Content-Type: application/json' \
  -d '{"text":"<script>alert(1)</script>"}' "$BASE/products/$prod_a/questions")"
[[ "$xss" == "422" ]] || fail "XSS pregunta -> $xss"

page="$(curl -sS -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $token_a" \
  "$BASE/questions?page_size=101")"
[[ "$page" == "422" ]] || fail "page_size 101 -> $page"

b2_on_a="$(code_of "$token_2" GET "/sells/$sell_1")"
[[ "$b2_on_a" == "404" ]] || fail "Buyer2 GET /sells/$sell_1 -> $b2_on_a"

echo "OK $BASE buyers=$buyer1,$buyer2 sells=$sell_1,$sell_2 products=$prod_a,$prod_hot,$prod_b"
rm -f "$png"
