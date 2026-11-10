import sqlite3

from rapidfuzz import fuzz, process

from acciones import apps
from config import BASE

RUTA = BASE / "datos" / "jarvis.db"
RUTA.parent.mkdir(exist_ok=True)
UMBRAL_APRENDIDO = 88     # qué tan parecida debe ser tu frase a una enseñada


def _sql(consulta, params=()):
    con = sqlite3.connect(RUTA)
    try:
        filas = con.execute(consulta, params).fetchall()
        con.commit()
        return filas
    finally:
        con.close()


_sql("CREATE TABLE IF NOT EXISTS comandos (frase TEXT PRIMARY KEY, tipo TEXT, destino TEXT)")
_sql("CREATE TABLE IF NOT EXISTS uso (frase TEXT PRIMARY KEY, veces INTEGER)")
_sql("CREATE TABLE IF NOT EXISTS fallidas (frase TEXT PRIMARY KEY, veces INTEGER)")


# ---------- enseñar y olvidar ----------
def ensenar(m):
    frase, verbo, destino = (g.strip() for g in m.groups())
    if verbo in ("abre", "abrir"):
        if not apps.buscar(destino):
            return f"No conozco {destino}. Agrégalo primero en el archivo de configuración."
        tipo, accion = "abrir", "abrir"
    elif verbo in ("cierra", "cerrar"):
        if not apps.buscar_proceso(destino):
            return f"No sé cerrar {destino}. Revisa su configuración."
        tipo, accion = "cerrar", "cerrar"
    elif verbo in ("presiona", "presionar"):
        combo = apps.combinacion(destino)
        if not combo:
            return "No entendí qué teclas presionar."
        tipo, accion = "presionar", "presionar"
        destino = combo
    else:
        tipo, accion = "responder", "responder"
    _sql("INSERT OR REPLACE INTO comandos VALUES (?, ?, ?)", (frase, tipo, destino))
    return f"Aprendido. Cuando digas {frase}, voy a {accion} {destino}."


def buscar_aprendido(t):
    """Si la frase se parece a un comando enseñado, lo ejecuta y devuelve la respuesta."""
    filas = _sql("SELECT frase, tipo, destino FROM comandos")
    if not filas:
        return None
    r = process.extractOne(t, [f[0] for f in filas], scorer=fuzz.ratio,
                           score_cutoff=UMBRAL_APRENDIDO)
    if not r:
        return None
    _, tipo, destino = filas[r[2]]
    if tipo == "abrir":
        return apps.abrir_destino(destino)
    if tipo == "cerrar":
        return apps.cerrar_destino(destino)
    if tipo == "presionar":
        return apps.presionar_combo(destino)
    return destino


def olvidar(m):
    frase = m.group(1).strip()
    filas = _sql("SELECT frase FROM comandos")
    r = process.extractOne(frase, [f[0] for f in filas], scorer=fuzz.ratio,
                           score_cutoff=UMBRAL_APRENDIDO) if filas else None
    if not r:
        return f"No tengo ningún comando llamado {frase}."
    _sql("DELETE FROM comandos WHERE frase = ?", (r[0],))
    return f"Olvidado: {r[0]}."


# ---------- historial ----------
def registrar_uso(frase):
    _sql("INSERT INTO uso VALUES (?, 1) ON CONFLICT(frase) DO UPDATE SET veces = veces + 1",
         (frase,))


def registrar_fallo(frase):
    _sql("INSERT INTO fallidas VALUES (?, 1) ON CONFLICT(frase) DO UPDATE SET veces = veces + 1",
         (frase,))


def mas_usados(m=None):
    filas = _sql("SELECT frase FROM uso ORDER BY veces DESC LIMIT 3")
    if not filas:
        return "Todavía no tengo suficientes datos."
    return "Lo que más me pides es: " + ", ".join(f[0] for f in filas) + "."


def no_entendidas(m=None):
    filas = _sql("SELECT frase FROM fallidas ORDER BY veces DESC LIMIT 3")
    if not filas:
        return "No tengo frases pendientes."
    return ("Lo que no he entendido es: " + ", ".join(f[0] for f in filas)
            + ". Puedes enseñarme qué hacer con ellas.")


def listar(m=None):
    filas = _sql("SELECT frase FROM comandos ORDER BY rowid DESC LIMIT 5")
    if not filas:
        return "Todavía no me has enseñado ningún comando."
    total = _sql("SELECT COUNT(*) FROM comandos")[0][0]
    return f"Me has enseñado {total} comandos. Los últimos son: " + ", ".join(f[0] for f in filas) + "."
