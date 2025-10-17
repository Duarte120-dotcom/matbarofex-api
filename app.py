from flask import Flask, jsonify
import requests
import time

app = Flask(__name__)

# Credenciales para obtener token automáticamente
USERNAME = "fduarte"
PASSWORD = "Numero120"

# Cache en memoria del token
ACCESS_TOKEN = None
ACCESS_EXP = 0  # epoch seconds (estimado)

# Símbolos válidos del MTR
SYMBOLS = [
    "I.BTC", "I.SOJA", "I.MAIZ", "I.TRIGO",
    "I.CCL", "I.RFX20", "I.ETH", "I.CAUCION"
]

TOKEN_URL = "https://api.matbarofex.com.ar/v2/token/"
SYMBOL_URL = "https://api.matbarofex.com.ar/v2/symbol/{symbol}"


def _now() -> int:
    return int(time.time())


def get_new_token():
    """Pide un nuevo access token a /v2/token/ usando username/password."""
    global ACCESS_TOKEN, ACCESS_EXP
    try:
        r = requests.post(
            TOKEN_URL,
            json={"username": USERNAME, "password": PASSWORD},
            timeout=12,
            headers={"Content-Type": "application/json"},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Token request failed: {r.status_code} {r.text}")

        data = r.json()
        ACCESS_TOKEN = data.get("access")
        # el access dura ~24h; dejamos margen de 23h
        ACCESS_EXP = _now() + 23 * 3600
        print("✅ Nuevo access token obtenido")
    except Exception as e:
        print("❌ Error obteniendo token:", e)
        ACCESS_TOKEN = None
        ACCESS_EXP = 0


def get_token():
    """Devuelve un access token válido; renueva si venció o no existe."""
    if ACCESS_TOKEN is None or _now() >= ACCESS_EXP:
        get_new_token()
    return ACCESS_TOKEN


def fetch_symbol(symbol: str, retry: bool = True):
    """Consulta /v2/symbol/<symbol>. Si 401, renueva token y reintenta una vez."""
    token = get_token()
    if not token:
        return {"symbol": symbol, "error": "no_token"}

    headers = {"Authorization": f"Bearer {token}"}
    url = SYMBOL_URL.format(symbol=symbol)
    r = requests.get(url, headers=headers, timeout=12)

    if r.status_code == 401 and retry:
        # token inválido/vencido → renuevo y reintento una vez
        get_new_token()
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"} if ACCESS_TOKEN else {}
        r = requests.get(url, headers=headers, timeout=12)

    try:
        data = r.json()
    except Exception:
        return {"symbol": symbol, "error": f"bad_json status={r.status_code}"}

    # si la API devuelve estructura de error, la propagamos con el símbolo
    if isinstance(data, dict) and "code" in data and data["code"] == "token_not_valid":
        return {"symbol": symbol, "error": "token_not_valid"}

    if isinstance(data, dict):
        data["symbol"] = symbol
    return data


@app.route("/")
def root():
    return {
        "status": "ok",
        "message": "Matba-Rofex proxy listo",
        "symbols": SYMBOLS,
        "endpoints": ["/symbol/<SYMBOL>", "/all"]
    }


@app.route("/symbol/<symbol>")
def symbol(symbol):
    return jsonify(fetch_symbol(symbol))


@app.route("/all")
def all_symbols():
    out = []
    for s in SYMBOLS:
        out.append(fetch_symbol(s))
    return jsonify(out)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
