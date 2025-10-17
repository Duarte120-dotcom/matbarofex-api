from flask import Flask, jsonify
import requests
import time

app = Flask(__name__)

USERNAME = "fduarte"
PASSWORD = "Numero120"

ACCESS_TOKEN = None
TOKEN_EXPIRATION = 0

SYMBOLS = [
    "I.TRIGO", "I.MAIZ", "I.SOJA", "I.CCL",
    "I.RFX20", "I.ETH", "I.BTC", "I.CAUCION"
]


def get_new_token():
    """Obtiene un nuevo token válido desde el endpoint correcto."""
    global ACCESS_TOKEN, TOKEN_EXPIRATION
    try:
        url = "https://api.matbarofex.com.ar/v2/token/"
        payload = {"username": USERNAME, "password": PASSWORD}
        headers = {"Content-Type": "application/json"}
        r = requests.post(url, json=payload, headers=headers, timeout=10)

        if r.status_code == 200:
            data = r.json()
            ACCESS_TOKEN = data.get("access")
            TOKEN_EXPIRATION = time.time() + 23 * 3600  # 23 h de validez
            print("✅ Nuevo token obtenido correctamente.")
        else:
            print("❌ Error al pedir token:", r.text)
            ACCESS_TOKEN = None
    except Exception as e:
        print("⚠️ Error de conexión al pedir token:", e)
        ACCESS_TOKEN = None


def get_token():
    """Devuelve un token válido o genera uno nuevo si está vencido."""
    if not ACCESS_TOKEN or time.time() > TOKEN_EXPIRATION:
        get_new_token()
    return ACCESS_TOKEN


def get_symbol_data(symbol):
    """Consulta un símbolo y renueva token automáticamente si hace falta."""
    token = get_token()
    if not token:
        return {"symbol": symbol, "error": "no_token"}

    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.matbarofex.com.ar/v2/symbol/{symbol}"
    r = requests.get(url, headers=headers, timeout=10)

    # Si devuelve 401, el token expiró → renovamos y reintentamos
    if r.status_code == 401:
        get_new_token()
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        r = requests.get(url, headers=headers, timeout=10)

    try:
        data = r.json()
    except Exception:
        return {"symbol": symbol, "error": f"Respuesta inválida ({r.status_code})"}

    if "code" in data and data["code"] == "token_not_valid":
        return {"symbol": symbol, "error": "token_not_valid"}

    data["symbol"] = symbol
    return data


@app.route("/")
def home():
    return jsonify({
        "status": "ok",
        "message": "Servidor Matba-Rofex funcionando correctamente",
        "endpoints": ["/symbol/I.TRIGO", "/all"]
    })


@app.route("/symbol/<symbol>")
def symbol(symbol):
    return jsonify(get_symbol_data(symbol))


@app.route("/all")
def all_symbols():
    results = []
    for s in SYMBOLS:
        results.append(get_symbol_data(s))
    return jsonify(results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

