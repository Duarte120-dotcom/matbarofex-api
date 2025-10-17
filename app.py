from flask import Flask, jsonify
import requests
import os
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
    if not ACCESS_TOKEN or time.time() > TOKEN_EXP:
        get_new_token()
    return ACCESS_TOKEN


def fetch_json(url):
    """Hace una solicitud GET autenticada."""
    token = get_token()
    if not token:
        return {"error": "no_token"}

    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers, timeout=20)

    if r.status_code == 401:
        get_new_token()
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        r = requests.get(url, headers=headers, timeout=20)

    try:
        return r.json()
    except Exception:
        return {"error": f"Invalid response {r.status_code}"}


@app.route("/")
def home():
    return jsonify({
        "status": "ok",
        "message": "Servidor proxy Matba-Rofex activo",
        "routes": ["/symbol/I.TRIGO", "/futures/TRIGO", "/crop/TRIGO"]
    })


@app.route("/symbol/<symbol>")
def symbol(symbol):
    """Devuelve info completa de un símbolo (spot o futuro)."""
    data = fetch_json(f"https://api.matbarofex.com.ar/v2/symbol/{symbol}")
    return jsonify(data)


@app.route("/futures/<base>")
def futures(base):
    """Devuelve todos los contratos futuros de un cultivo."""
    base = base.upper()
    instruments = fetch_json("https://api.matbarofex.com.ar/v2/instrument/")
    if not isinstance(instruments, list):
        return jsonify({"error": "no_data", "data": instruments})

    filtered = [
        i for i in instruments
        if base in i.get("symbol", "") and not i["symbol"].startswith("I.")
    ]
    return jsonify(filtered)


@app.route("/crop/<base>")
def crop(base):
    """Devuelve disponible y futuros del cultivo."""
    base = base.upper()
    result = {"base": base, "spot": None, "futures": []}

    # Spot
    spot = fetch_json(f"https://api.matbarofex.com.ar/v2/symbol/I.{base}")
    result["spot"] = spot

    # Futuros
    futures_data = fetch_json(f"https://matbarofex-proxy.onrender.com/futures/{base}")
    result["futures"] = futures_data

    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
