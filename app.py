from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

# TOKEN de acceso (actual)
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzYwODAwOTMyLCJpYXQiOjE3NjA3MTQ1MzIsImp0aSI6ImQ3YTJhOGIwZmJkMzQyZDE5NzRiZjY5MDRmNWExN2JiIiwidXNlcl9pZCI6NDc2fQ.fYU60aUKGHipGQptszDArCxC39vVjJqAAg9AhJbCA5E"

@app.route("/")
def home():
    return {"status": "ok", "message": "Servidor funcionando. Usa /symbol/<nombre> para consultar."}

@app.route("/symbol/<symbol>")
def get_symbol(symbol):
    """Consulta un símbolo en la API de Matba-Rofex."""
    try:
        url = f"https://api.matbarofex.com.ar/v2/symbol/{symbol}"
        headers = {"Authorization": f"Bearer {TOKEN}"}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
