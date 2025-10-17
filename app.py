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
        "routes": ["/symbol/I.TRIGO", "/futures/TRIGO", "/crop/TRIGO"]
    })


@app.route("/symbol/<symbol>")
def symbol(symbol):
    return jsonify(fetch_json(f"https://api.matbarofex.com.ar/v2/symbol/{symbol}"))


@app.route("/futures/<base>")
def futures(base):
    """Devuelve los contratos futuros conocidos de un cultivo"""
    base = base.upper()
    # Futuros conocidos (podés agregar más símbolos si aparecen nuevos)
    known_futures = {
        "TRIGO": ["TRIGONov25", "TRIGODic25", "TRIGOEne26"],
        "MAIZ": ["MAIZNov25", "MAIZDic25", "MAIZEne26"],
        "SOJA": ["SOJANov25", "SOJADic25", "SOJAEne26"]
    }

    if base not in known_futures:
        return jsonify({"error": f"No hay futuros definidos para {base}"})

    result = []
    for symbol in known_futures[base]:
        data = fetch_json(f"https://api.matbarofex.com.ar/v2/symbol/{symbol}")
        data["symbol"] = symbol
        result.append(data)
    return jsonify(result)


@app.route("/crop/<base>")
def crop(base):
    base = base.upper()
    return jsonify({
        "spot": fetch_json(f"https://api.matbarofex.com.ar/v2/symbol/I.{base}"),
        "futures": fetch_json(f"https://matbarofex-proxy.onrender.com/futures/{base}")
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
