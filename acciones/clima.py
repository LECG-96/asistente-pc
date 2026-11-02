import json
import urllib.request
from urllib.parse import urlencode

from config import CFG

CIUDAD = CFG.get("ciudad", {"nombre": "Santiago", "lat": -33.45, "lon": -70.66})

CODIGOS = {
    0: "despejado", 1: "mayormente despejado", 2: "parcialmente nublado", 3: "nublado",
    45: "con niebla", 48: "con niebla",
    51: "con llovizna", 53: "con llovizna", 55: "con llovizna",
    56: "con llovizna helada", 57: "con llovizna helada",
    61: "con lluvia ligera", 63: "con lluvia", 65: "con lluvia fuerte",
    66: "con lluvia helada", 67: "con lluvia helada",
    71: "con nieve ligera", 73: "con nieve", 75: "con nieve fuerte", 77: "con granizo fino",
    80: "con chubascos", 81: "con chubascos", 82: "con chubascos fuertes",
    85: "con nevazón", 86: "con nevazón fuerte",
    95: "con tormenta", 96: "con tormenta y granizo", 99: "con tormenta y granizo",
}


def _consultar():
    params = urlencode({
        "latitude": CIUDAD["lat"],
        "longitude": CIUDAD["lon"],
        "current": "temperature_2m,apparent_temperature,weather_code",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "timezone": "auto",
        "forecast_days": 2,
    })
    with urllib.request.urlopen(f"https://api.open-meteo.com/v1/forecast?{params}", timeout=6) as r:
        return json.load(r)


def _grados(n):
    n = round(n)
    return f"{n} grado" if abs(n) == 1 else f"{n} grados"


def _lluvia(prob):
    if prob is None:
        return ""
    if prob >= 30:
        return f" Hay {round(prob)} por ciento de probabilidad de lluvia."
    return " Es poco probable que llueva."


def clima(m):
    texto = m.string
    try:
        d = _consultar()
        dia = 1 if "manana" in texto else 0
        diario = d["daily"]
        prob = diario["precipitation_probability_max"][dia]
        desc = CODIGOS.get(diario["weather_code"][dia], "")
        maxima, minima = diario["temperature_2m_max"][dia], diario["temperature_2m_min"][dia]

        if any(p in texto for p in ("llover", "lluvia")):
            cuando = "Mañana" if dia else "Hoy"
            return f"{cuando}:" + (_lluvia(prob) or " No tengo datos de lluvia.")

        if dia == 1:
            return (f"Mañana, {desc}. Máxima de {_grados(maxima)} y mínima de {_grados(minima)}."
                    + _lluvia(prob))

        actual = d["current"]
        return (f"Ahora hay {_grados(actual['temperature_2m'])}, "
                f"{CODIGOS.get(actual['weather_code'], desc)}. "
                f"Sensación térmica de {_grados(actual['apparent_temperature'])}. "
                f"Hoy la máxima será de {_grados(maxima)} y la mínima de {_grados(minima)}."
                + _lluvia(prob))
    except Exception:
        return "El servicio del clima no respondió."