from flask import Flask, jsonify
import requests
import time

app = Flask(__name__)

USERNAME = "fduarte"
PASSWORD = "Numero120"

ACCESS_TOKEN = None
TOKEN_EXP = 0

# Lista completa de símbolos que querés tener disponibles
SYMBOLS = ["I.TRIGO", "I.MAIZ", "I.SOJA", "I.CCL", "I.RFX20", "I.ETH", "I.BTC"]

def get_new_token():
    """Pide un nuevo token válido desde el endpoint oficial de Matba-Rofex."""
    global ACCESS_TOKEN, TOKEN_EXP
    try:
        r = requests.post(
            "https://api.matbarofex.com.ar/v2/token/",
            json={"username": USERNAME, "password": PASSWORD},
            timeout=10
        )
        if r.status_code == 200:
            ACCESS_TOKEN = r.json().get("access")
            TOKEN_EXP = time.time() + 23 * 3600  # válido por ~23 h
            print("✅ Nuevo token obtenido correctamente.")
        else:
            print("❌ Error al obtener token:", r.text)
            ACCESS_TOKEN = None
    except Exception as e:
        print("⚠️ Error de conexión al pedir token:", e)
        ACCESS_TOKEN = None


def get_token():
    """Devuelve un token válido o lo renueva si expiró."""
    if not ACCESS_TOKEN or time.time() > TOKEN_EXP:
        get_new_token()
    return ACCESS_TOKEN


def fetch_symbol(symbol):
    """Devuelve la información de un símbolo (con reintento)."""
    token = get_token()
    if not token:
        return {"symbol": symbol, "error": "no_token"}

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
        return {"symbol": symbol, "error": f"invalid_response_{r.status_code}"}

    # Si la API devuelve permiso denegado, lo avisamos claramente
    if isinstance(data, dict) and data.get("detail", "").startswith("You do not have permission"):
        return {"symbol": symbol, "error": "no_permission"}

    data["symbol"] = symbol
    return data


@app.route("/")
def home():
    return jsonify({
        "status": "ok",
        "symbols": SYMBOLS,
        "example": "https://matbarofex-proxy.onrender.com/symbol/I.TRIGO"
    })


@app.route("/symbol/<symbol>")
def symbol(symbol):
    """Endpoint individual para cada símbolo."""
    return jsonify(fetch_symbol(symbol))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

