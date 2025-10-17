from flask import Flask, jsonify
import requests
import time

app = Flask(__name__)

# Credenciales
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
    """Consulta una URL con token válido."""
    token = get_token()
    if not token:
        return {"error": "no_token"}

    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers, timeout=15)

    if r.status_code == 401:
        get_new_token()
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        r = requests.get(url, headers=headers, timeout=15)

    try:
        return r.json()
    except Exception:
        return {"error": f"Invalid response {r.status_code}"}


@app.route("/spot/<base_symbol>")
def spot(base_symbol):
    """Devuelve el valor spot de un cultivo (I.TRIGO, I.SOJA, etc.)"""
    base = base_symbol.upper()
    symbol = f"I.{base}"
    data = fetch_json(f"https://api.matbarofex.com.ar/v2/symbol/{symbol}")
    return jsonify(data)


@app.route("/futures/<base_symbol>")
def futures(base_symbol):
    """Devuelve los futuros individuales del cultivo."""
    base = base_symbol.upper()
    all_instruments = fetch_json("https://api.matbarofex.com.ar/v2/instrument/")
    if not isinstance(all_instruments, list):
        return jsonify({"error": "invalid_response", "data": all_instruments})

    # Filtrar futuros de ese cultivo
    futures_list = [
        i for i in all_instruments
        if base in i.get("symbol", "") and not i.get("symbol", "").startswith("I.")
    ]

    detailed = []
    for f in futures_list:
        sym = f.get("symbol")
        if sym:
            info = fetch_json(f"https://api.matbarofex.com.ar/v2/symbol/{sym}")
            if isinstance(info, dict):
                info["symbol"] = sym
                detailed.append(info)

    return jsonify(detailed)


@app.route("/all_futures")
def all_futures():
    """Devuelve todos los futuros conocidos (para todos los cultivos)."""
    instruments = fetch_json("https://api.matbarofex.com.ar/v2/instrument/")
    if not isinstance(instruments, list):
        return jsonify({"error": "invalid_response", "data": instruments})

    result = []
    for inst in instruments:
        sym = inst.get("symbol")
        if sym and not sym.startswith("I."):
            info = fetch_json(f"https://api.matbarofex.com.ar/v2/symbol/{sym}")
            if isinstance(info, dict):
                info["symbol"] = sym
                result.append(info)

    return jsonify(result)
