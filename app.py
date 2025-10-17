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
    base = base_symbol.upper()
    all_instruments = fetch_json("https://api.matbarofex.com.ar/v2/instrument/")
    if not isinstance(all_instruments, list):
        return jsonify({"error": "invalid_response", "data": all_instruments})

    futures_filtered = [
        i for i in all_instruments
        if base in i.get("symbol", "")
    ]
    return jsonify(futures_filtered)


@app.route("/crop/<base_symbol>")
def crop(base_symbol):
    """Devuelve el disponible (spot) y todos los futuros de un cultivo."""
    base = base_symbol.upper()
    result = {"base": base, "spot": None, "futures": []}

    # Spot
    spot_symbol = f"I.{base}"
    spot = fetch_json(f"https://api.matbarofex.com.ar/v2/symbol/{spot_symbol}")
    result["spot"] = spot

    # Futuros
    all_instruments = fetch_json("https://api.matbarofex.com.ar/v2/instrument/")
    if isinstance(all_instruments, list):
        futures_data = []
        for inst in all_instruments:
            sym = inst.get("symbol")
            if sym and base in sym and not sym.startswith("I."):
                data_fut = fetch_json(f"https://api.matbarofex.com.ar/v2/symbol/{sym}")
                if isinstance(data_fut, dict):
                    data_fut["symbol"] = sym
                    futures_data.append(data_fut)
        result["futures"] = futures_data
    else:
        result["futures_error"] = all_instruments

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
