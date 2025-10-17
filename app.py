from flask import Flask, jsonify
import requests
import time

app = Flask(__name__)

USERNAME = "fduarte"
PASSWORD = "Numero120"

ACCESS_TOKEN = None
TOKEN_EXP = 0

# Solo símbolos accesibles sin permisos especiales
SYMBOLS = ["I.TRIGO", "I.MAIZ", "I.CCL", "I.RFX20", "I.ETH", "I.BTC"]

def get_new_token():
    """Obtiene un token de MatbaRofex."""
    global ACCESS_TOKEN, TOKEN_EXP
    try:
        url = "https://api.matbarofex.com.ar/v2/token/"
        payload = {"username": USERNAME, "password": PASSWORD}
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            ACCESS_TOKEN = r.json().get("access")
            TOKEN_EXP = time.time() + 23 * 3600
            print("✅ Nuevo token generado correctamente.")
        else:
            print("❌ Error al generar token:", r.text)
            ACCESS_TOKEN = None
    except Exception as e:
        print("⚠️ Error al conectar:", e)
        ACCESS_TOKEN = None


def get_token():
    if not ACCESS_TOKEN or time.time() > TOKEN_EXP:
        get_new_token()
    return ACCESS_TOKEN


def fetch_symbol(symbol):
    """Devuelve un símbolo, reintentando si el token vence."""
    token = get_token()
    if not token:
        return {"symbol": symbol, "error": "token_missing"}

    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.matbarofex.com.ar/v2/symbol/{symbol}"
    r = requests.get(url, headers=headers, timeout=10)

    if r.status_code == 401:  # token vencido
        get_new_token()
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        r = requests.get(url, headers=headers, timeout=10)

    try:
        data = r.json()
    except Exception:
        return {"symbol": symbol, "error": "invalid_json"}

    # Filtramos errores de permisos (Power BI los interpretaba mal)
    if isinstance(data, dict) and data.get("detail", "").startswith("You do not have permission"):
        return {"symbol": symbol, "error": "no_permission"}

    data["symbol"] = symbol
    return data


@app.route("/")
def home():
    return jsonify({"status": "ok", "message": "Servidor listo", "symbols": SYMBOLS})


@app.route("/all")
def all_data():
    """Combina todos los símbolos accesibles en una lista JSON simple."""
    results = []
    for s in SYMBOLS:
        results.append(fetch_symbol(s))
    # Power BI necesita JSON plano, no anidado
    return jsonify(results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)


