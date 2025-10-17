from flask import Flask, jsonify
import requests
import time

app = Flask(__name__)

USERNAME = "fduarte"
PASSWORD = "Numero120"

ACCESS_TOKEN = None
TOKEN_EXP = 0


def get_new_token():
    """Solicita un nuevo token al servidor de Matba-Rofex."""
    global ACCESS_TOKEN, TOKEN_EXP
    try:
        r = requests.post(
            "https://api.matbarofex.com.ar/v2/token/",
            json={"username": USERNAME, "password": PASSWORD},
            timeout=10
        )
        if r.status_code == 200:
            ACCESS_TOKEN = r.json().get("access")
            TOKEN_EXP = time.time() + 23 * 3600
            print("✅ Nuevo token obtenido.")
        else:
            print("❌ Error al obtener token:", r.text)
            ACCESS_TOKEN = None
    except Exception as e:
        print("⚠️ Error solicitando token:", e)
        ACCESS_TOKEN = None


def get_token():
    """Devuelve un token válido."""
    if not ACCESS_TOKEN or time.time() > TOKEN_EXP:
        get_new_token()
    return ACCESS_TOKEN


def fetch_json(url):
    """Consulta una URL con el token activo."""
    token = get_token()
    if not token:
        return {"error": "no_token"}

    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers, timeout=10)

    if r.status_code == 401:
        get_new_token()
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        r = requests.get(url, headers=headers, timeout=10)

    try:
        return r.json()
    except Exception:
        return {"error": f"Invalid response {r.status_code}"}


@app.route("/")
def home():
    return jsonify({
        "status": "ok",
        "message": "Proxy Matba-Rofex funcionando.",
        "examples": [
            "/symbol/I.TRIGO",
            "/futures/TRIGO",
            "/crop/TRIGO"
        ]
    })


@app.route("/symbol/<symbol>")
def symbol(symbol):
    """Devuelve la información completa de un símbolo (spot o futuro)."""
    data = fetch_json(f"https://api.matbarofex.com.ar/v2/symbol/{symbol}")
    return jsonify(data)


@app.route("/futures/<base_symbol>")
def futures(base_symbol):
    """Devuelve todos los contratos futuros de un cultivo base."""
    data = fetch_json(f"https://api.matbarofex.com.ar/v2/instruments/{base_symbol.upper()}/")
    return jsonify(data)


@app.route("/crop/<base_symbol>")
def crop(base_symbol):
    """Devuelve el disponible y todos los futuros de un cultivo."""
    base = base_symbol.upper()
    result = {"base": base, "spot": None, "futures": []}

    # Spot
    spot_symbol = f"I.{base}"
    spot = fetch_json(f"https://api.matbarofex.com.ar/v2/symbol/{spot_symbol}")
    result["spot"] = spot

    # Futuros
    futs = fetch_json(f"https://api.matbarofex.com.ar/v2/instruments/{base}/")
    if isinstance(futs, list):
        futures_data = []
        for f in futs:
            symbol_name = f.get("symbol")
            if symbol_name:
                future_data = fetch_json(f"https://api.matbarofex.com.ar/v2/symbol/{symbol_name}")
                future_data["symbol"] = symbol_name
                futures_data.append(future_data)
        result["futures"] = futures_data
    else:
        result["futures_error"] = futs

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

