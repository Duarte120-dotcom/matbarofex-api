from flask import Flask, jsonify
import requests
import time

app = Flask(__name__)

# Credenciales (solo se usan dentro del servidor, seguras)
USERNAME = "fduarte"
PASSWORD = "Numero120"

# Token cacheado en memoria
ACCESS_TOKEN = None
TOKEN_EXPIRES_AT = 0

# Lista de índices del Matba-Rofex
SYMBOLS = [
    "I.TRIGO", "I.MAIZ", "I.SOJA", "I.CCL", "I.RFX20",
    "I.ETH", "I.BTC", "I.CAUCI", "I.CAU", "I.DLR"
]


def get_new_token():
    """Solicita un nuevo token de acceso a la API de Matba-Rofex."""
    global ACCESS_TOKEN, TOKEN_EXPIRES_AT
    url = "https://api.matbarofex.com.ar/auth/token/"
    data = {"username": USERNAME, "password": PASSWORD}
    try:
        r = requests.post(url, json=data, timeout=10)
        if r.status_code == 200:
            ACCESS_TOKEN = r.json().get("access")
            # expira en ~12 horas
            TOKEN_EXPIRES_AT = time.time() + 11 * 3600
            print("✅ Nuevo token obtenido correctamente.")
        else:
            print("⚠️ Error al obtener token:", r.text)
    except Exception as e:
        print("❌ Error al pedir token:", e)


def get_token():
    """Devuelve el token válido, renovándolo si venció."""
    global ACCESS_TOKEN
    if ACCESS_TOKEN is None or time.time() > TOKEN_EXPIRES_AT:
        get_new_token()
    return ACCESS_TOKEN


def get_symbol_data(symbol):
    """Consulta un símbolo de la API con token actualizado."""
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.matbarofex.com.ar/v2/symbol/{symbol}"
    r = requests.get(url, headers=headers, timeout=10)
    return r.json()


@app.route("/")
def home():
    return {
        "status": "ok",
        "message": "Servidor Matba-Rofex funcionando. Usa /symbol/<nombre> o /all"
    }


@app.route("/symbol/<symbol>")
def symbol(symbol):
    """Consulta un símbolo específico."""
    try:
        data = get_symbol_data(symbol)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/all")
def all_symbols():
    """Devuelve todos los índices en una sola tabla JSON."""
    results = []
    for s in SYMBOLS:
        try:
            data = get_symbol_data(s)
            if isinstance(data, dict):
                data["symbol"] = s
                results.append(data)
        except Exception as e:
            results.append({"symbol": s, "error": str(e)})
    return jsonify(results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
