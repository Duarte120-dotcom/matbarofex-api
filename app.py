@app.route("/futures/<base_symbol>")
def futures(base_symbol):
    """Devuelve todos los contratos futuros de un cultivo base."""
    base = base_symbol.upper()
    all_instruments = fetch_json("https://api.matbarofex.com.ar/v2/instrument/")
    
    if not isinstance(all_instruments, list):
        return jsonify({"error": "invalid_response", "data": all_instruments})
    
    # Filtramos solo los símbolos que contienen el nombre base (ej. TRIGO)
    futures_filtered = [
        i for i in all_instruments
        if base in i.get("symbol", "")
    ]
    return jsonify(futures_filtered)


@app.route("/crop/<base_symbol>")
def crop(base_symbol):
    """Devuelve el disponible y todos los futuros de un cultivo."""
    base = base_symbol.upper()
    result = {"base": base, "spot": None, "futures": []}

    # Spot
    spot_symbol = f"I.{base}"
    spot = fetch_json(f"https://api.matbarofex.com.ar/v2/symbol/{spot_symbol}")
    result["spot"] = spot

    # Futuros (filtrados)
    all_instruments = fetch_json("https://api.matbarofex.com.ar/v2/instrument/")
    if isinstance(all_instruments, list):
        futures_data = []
        for i in all_instruments:
            sym = i.get("symbol")
            if sym and base in sym and not sym.startswith("I."):
                future_data = fetch_json(f"https://api.matbarofex.com.ar/v2/symbol/{sym}")
                if isinstance(future_data, dict):
                    futures_data.append(future_data)
        result["futures"] = futures_data
    else:
        result["futures_error"] = all_instruments

    return jsonify(result)
