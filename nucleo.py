# nucleo.py
# Núcleo del juego con el flujo de REPARTO DE PRESUPUESTO.
#
# Flujo:  iniciar_mision -> repartir (varias veces) -> revisar -> simular
#         -> puntaje / revelar
#
# Reglas:
#  - Cada recurso tiene un MÍNIMO y un ÓPTIMO ocultos (vienen de
#    datos/parametros_misiones.json, que llena Chambi).
#  - El jugador reparte dinero (M USD). valor = dinero * tasa del recurso, salvo
#    propulsión y potencia, que usan física real (bloque "fisica" en el JSON).
#  - Si algún valor queda bajo su mínimo, la misión falla.
#  - Si no falla, el puntaje depende de qué tan cerca está cada valor del óptimo.
#
# La interfaz (Gonzalo) SOLO llama a estas funciones. No lee mínimos ni óptimos
# directamente: usa recursos_visibles() mientras reparte y revelar() al final.

import copy
import json
import math
import random
import itertools
from pathlib import Path

import fisica
import potencia_costo

CARPETA_DATOS = Path(__file__).parent / "datos"
ARCHIVO_PARAMETROS = "parametros_misiones.json"
ARCHIVO_DESTINOS = "destinos.json"

# Qué le pasa a la nave cuando un recurso queda bajo su mínimo (campo "falla" de cada
# recurso): estructura -> explota, propulsión -> no_llega, potencia -> se_apaga,
# comunicaciones -> incomunicada, datos -> sin_ciencia, tiempo -> fuera_de_tiempo.
FALLAS_VALIDAS = ["explota", "no_llega", "se_apaga", "incomunicada", "sin_ciencia", "fuera_de_tiempo"]
MARGEN_OPTIMO = 0.10   # un recurso es "óptimo" si está a ±10 % de su óptimo (Justin puede cambiarlo)
TOLERANCIA = 1e-9      # evita errores de redondeo al comparar números decimales


# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------

def cargar_destinos(ruta=None):
    """Lee destinos.json y devuelve {nombre_destino: datos}. {} si no existe."""
    ruta = Path(ruta) if ruta else CARPETA_DATOS / ARCHIVO_DESTINOS
    if not ruta.exists():
        return {}
    with open(ruta, encoding="utf-8") as f:
        return {d["destino"]: d for d in json.load(f)}


def delta_v_nave(destino, destinos=None):
    """Delta-v que debe aportar la NAVE (m/s) = delta-v del destino - delta-v de
    llegar a LEO (lo pone el cohete). Sale de destinos.json, no se escribe a mano.
    Para LEO vale 0: ahí el mínimo de propulsión se queda en el JSON."""
    destinos = destinos if destinos is not None else cargar_destinos()
    if destino not in destinos or "LEO" not in destinos:
        raise ValueError(f"Destino desconocido en destinos.json: '{destino}'")
    return max(0.0, destinos[destino]["delta_v_m_s"] - destinos["LEO"]["delta_v_m_s"])


_CAMPOS_PROPULSION = ("isp_s", "masa_seca_kg", "musd_por_kg_propelente")
_CAMPOS_POTENCIA = ("eficiencia_panel", "musd_por_m2_panel")


def preparar_parametros(m, ruta_destinos=None):
    """Devuelve una COPIA de la misión lista para jugar:
      1. Si la misión trae los datos físicos de Chambi a nivel de misión
         (isp_s, masa_seca_kg, musd_por_kg_propelente / eficiencia_panel,
         musd_por_m2_panel), crea el bloque "fisica" de los recursos
         propulsion y potencia (salvo que ya tengan uno propio).
      2. Con destinos.json: el mínimo de propulsión pasa a ser
         delta_v_nave(destino) (si es mayor que 0) y la potencia recibe la
         distancia al Sol (distancia_ua) del destino.
    Es idempotente: se puede llamar varias veces."""
    m = copy.deepcopy(m)
    for r in m.get("recursos") or []:
        if "fisica" in r:
            continue
        if r.get("clave") == "propulsion" and all(k in m for k in _CAMPOS_PROPULSION):
            r["fisica"] = {"tipo": "propulsion", "isp_s": m["isp_s"],
                           "m_seca_kg": m["masa_seca_kg"],
                           "musd_por_kg_propelente": m["musd_por_kg_propelente"]}
        elif r.get("clave") == "potencia" and all(k in m for k in _CAMPOS_POTENCIA):
            r["fisica"] = {"tipo": "potencia", "musd_por_m2": m["musd_por_m2_panel"],
                           "eficiencia": m["eficiencia_panel"], "distancia_ua": None}
    destinos = cargar_destinos(ruta_destinos)
    d = destinos.get(m.get("destino"))
    if not d:
        return m
    for r in m.get("recursos") or []:
        f = r.get("fisica")
        if not isinstance(f, dict):
            continue
        if f.get("tipo") == "potencia" and "distancia_ua" in d:
            f["distancia_ua"] = d["distancia_ua"]
        if f.get("tipo") == "propulsion":
            dv = delta_v_nave(m["destino"], destinos)
            if dv > 0:
                r["minimo"] = dv
    return m


def cargar_parametros(mision_id, ruta=None):
    """Lee parametros_misiones.json y devuelve el diccionario de esa misión
    (ya preparado con los datos de destinos.json, ver preparar_parametros).
    El archivo es una lista de misiones; cada una tiene la clave "mision"."""
    ruta = Path(ruta) if ruta else CARPETA_DATOS / ARCHIVO_PARAMETROS
    with open(ruta, encoding="utf-8") as f:
        misiones = json.load(f)
    for m in misiones:
        if m["mision"] == mision_id:
            return preparar_parametros(m)
    disponibles = [m["mision"] for m in misiones]
    raise ValueError(f"Misión desconocida: '{mision_id}'. Disponibles: {disponibles}")


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------

def iniciar_mision(parametros):
    """Crea el estado de una misión nueva a partir de sus parámetros.
    Devuelve: diccionario 'estado'."""
    parametros = preparar_parametros(parametros)
    return {
        "mision": parametros["mision"],
        "destino": parametros["destino"],
        "cohete": parametros["cohete"],
        "presupuesto_musd": parametros["presupuesto_musd"],
        "pistas": list(parametros.get("pistas", [])),
        "recursos": parametros["recursos"],     # incluye mínimos y óptimos: NO mostrarlos
        "reparto": {r["clave"]: 0.0 for r in parametros["recursos"]},   # M USD por recurso
        "fase": "reparto",                      # reparto, simulacion, resultado
        "resultado": None,
        "umbrales_estrellas": umbrales_estrellas(parametros),   # puntaje para 2, 3, 4 y 5 estrellas
    }


def _buscar_recurso(estado, clave):
    for r in estado["recursos"]:
        if r["clave"] == clave:
            return r
    claves = [r["clave"] for r in estado["recursos"]]
    raise ValueError(f"Recurso desconocido: '{clave}'. Disponibles: {claves}")


# ---------------------------------------------------------------------------
# Conversión dinero -> valor del recurso
# ---------------------------------------------------------------------------

def convertir(recurso, dinero_musd):
    """Cuánto del recurso compra ese dinero.
    - Con bloque "fisica" tipo "propulsion": el dinero compra propelente
      (dinero / musd_por_kg_propelente) y el delta-v sale de
      fisica.delta_v(isp_s, m_seca + m_prop, m_seca)  [m/s].
    - Con bloque "fisica" tipo "potencia": el dinero compra área de panel
      (dinero / musd_por_m2) y la potencia sale de
      potencia_costo.potencia_generada(distancia_ua, area, eficiencia)  [W].
    - Sin bloque "fisica": lineal, valor = dinero / musd_por_unidad."""
    f = recurso.get("fisica")
    if f and f["tipo"] == "propulsion":
        m_prop = dinero_musd / f["musd_por_kg_propelente"]
        m_seca = f["m_seca_kg"]
        return fisica.delta_v(f["isp_s"], m_seca + m_prop, m_seca)
    if f and f["tipo"] == "potencia":
        area = dinero_musd / f["musd_por_m2"]
        return potencia_costo.potencia_generada(f["distancia_ua"], area, f["eficiencia"])
    return dinero_musd / recurso["musd_por_unidad"]


def costo_de(recurso, valor):
    """Inversa de convertir: cuántos M USD cuesta alcanzar ese valor del recurso.
    La usa verificar_parametros para saber cuánto cuestan los mínimos y óptimos."""
    f = recurso.get("fisica")
    if f and f["tipo"] == "propulsion":
        m_prop = fisica.masa_propelente(valor, f["isp_s"], f["m_seca_kg"])
        return m_prop * f["musd_por_kg_propelente"]
    if f and f["tipo"] == "potencia":
        w_por_m2 = potencia_costo.potencia_generada(f["distancia_ua"], 1.0, f["eficiencia"])
        return valor / w_por_m2 * f["musd_por_m2"]
    return valor * recurso["musd_por_unidad"]


def valor_recurso(estado, clave):
    """Valor actual del recurso según el dinero que se le asignó."""
    return convertir(_buscar_recurso(estado, clave), estado["reparto"][clave])


def cotizar(estado, clave, valor):
    """Cuántos M USD cuesta tener 'valor' del recurso 'clave' (en su unidad: kg, m/s, W...).
    La usa la interfaz en cada estación: el jugador escribe la CANTIDAD y ve su costo.
    Es la inversa de convertir (usa costo_de). ValueError si valor < 0 o la clave no existe."""
    if valor < 0:
        raise ValueError("La cantidad no puede ser negativa")
    return costo_de(_buscar_recurso(estado, clave), valor)


def repartir_valor(estado, clave, valor):
    """Atajo: asigna al recurso el dinero que cuesta 'valor' (repartir + cotizar).
    Devuelve el costo en M USD."""
    costo = cotizar(estado, clave, valor)
    repartir(estado, clave, costo)
    return costo


# ---------------------------------------------------------------------------
# Fase 1: reparto y revisión
# ---------------------------------------------------------------------------

def repartir(estado, clave, dinero_musd):
    """Asigna dinero (M USD) a un recurso. No bloquea si se pasa del presupuesto:
    eso lo avisa revisar(), como en el flujo."""
    if estado["fase"] != "reparto":
        raise ValueError("Solo se puede repartir en la fase 'reparto'")
    if dinero_musd < 0:
        raise ValueError("El dinero no puede ser negativo")
    _buscar_recurso(estado, clave)          # valida que exista
    estado["reparto"][clave] = float(dinero_musd)
    return estado


def gasto_total(estado):
    return sum(estado["reparto"].values())


def presupuesto_restante(estado):
    """M USD sin repartir (negativo si se pasó)."""
    return estado["presupuesto_musd"] - gasto_total(estado)


PASOS_DINERO = [10, 5, 4, 2.5, 2, 1, 0.5, 0.25, 0.1]    # M USD, de mayor a menor


def paso_dinero(estado):
    """Paso (M USD) que debe usar la interfaz en los botones − y + de esa misión.
    Es el paso 'redondo' más grande que cumple las tres condiciones:
      1. divide exacto el presupuesto (se puede gastar todo);
      2. da al menos 25 pasos;
      3. permite comprar TODOS los mínimos sin pasarse del presupuesto.
    Un paso fijo no sirve: con pasos de 5 M USD, Easy (14.5 M USD) sería imposible,
    porque sus mínimos cuestan ~11 y habría que gastar 15.
    Usar: repartir(estado, clave, round(dinero_actual + paso_dinero(estado), 6))."""
    pres = estado["presupuesto_musd"]
    costos = [costo_de(r, r["minimo"]) for r in estado["recursos"]]

    def divide(p):
        n = pres / p
        return abs(n - round(n)) < 1e-6

    def alcanza(p):
        return sum(math.ceil(c / p - 1e-9) * p for c in costos) <= pres + TOLERANCIA

    for min_pasos in (25, 1):
        for p in PASOS_DINERO:
            if divide(p) and pres / p >= min_pasos and alcanza(p):
                return float(p)
    return 0.1


def recursos_visibles(estado):
    """Lo que la interfaz puede mostrar MIENTRAS el jugador reparte
    (sin mínimos ni óptimos). Devuelve lista de dicts."""
    return [{"clave": r["clave"], "unidad": r["unidad"],
             "dinero_musd": estado["reparto"][r["clave"]],
             "valor": valor_recurso(estado, r["clave"])}
            for r in estado["recursos"]]


def revisar(estado):
    """CML 4: solo verifica que el reparto no supere el presupuesto.
    Devuelve: {'ok': bool, 'exceso_musd': float, 'mensaje': None o texto}.
    Si ok, pasa a 'simulacion'. Si no, 'mensaje' explica que se pasó del presupuesto."""
    exceso = gasto_total(estado) - estado["presupuesto_musd"]
    ok = exceso <= TOLERANCIA
    if ok:
        estado["fase"] = "simulacion"
    return {"ok": ok, "exceso_musd": max(exceso, 0.0),
            "mensaje": None if ok else mensaje_presupuesto(estado)}


# ---------------------------------------------------------------------------
# Fase 2: simulación
# ---------------------------------------------------------------------------

def simular(estado):
    """Compara cada valor con su mínimo. Guarda y devuelve el resultado:
    {'exito': bool, 'falla': None o 'explota'/'no_llega'/..., 'fallas': [...],
     'bajo_minimo': [claves]}.
    Éxito = ningún recurso quedó bajo su mínimo. Si fallan varios, TODOS cuentan por
    igual: 'bajo_minimo' y 'fallas' los listan en el orden del JSON. 'falla' es solo
    la primera de 'fallas' (se mantiene por compatibilidad; usar 'fallas')."""
    if estado["fase"] != "simulacion":
        raise ValueError("Primero hay que pasar la revisión (revisar)")
    bajo = [r["clave"] for r in estado["recursos"]
            if valor_recurso(estado, r["clave"]) < r["minimo"] - TOLERANCIA]
    fallas = [_buscar_recurso(estado, c)["falla"] for c in bajo]
    estado["resultado"] = {"exito": not bajo, "falla": fallas[0] if fallas else None,
                           "fallas": fallas, "bajo_minimo": bajo}
    estado["fase"] = "resultado"
    return estado["resultado"]


# ---------------------------------------------------------------------------
# Mensajes (mensajes.json de Justin)
# ---------------------------------------------------------------------------
# datos/mensajes.json es un diccionario {clave: plantilla}. Las plantillas usan
# campos entre llaves, por ejemplo {destino} o {dv_requerido_m_s}.
#
# Qué clave se usa según cómo terminó la misión:
#   éxito                   -> "exito"
#   falla "no_llega"        -> "delta_v_insuficiente"   (propulsión bajo el mínimo)
#   falla "se_apaga"        -> "potencia_insuficiente"  (potencia bajo el mínimo)
#   cualquier otra falla    -> la clave con el nombre de la falla
#                              ("explota", "incomunicada", "sin_ciencia", "fuera_de_tiempo")
#   presupuesto excedido    -> "presupuesto_excedido"   (lo devuelve revisar)
#   "falla_aleatoria" y "masa_excede_lanzador" aún no los usa el núcleo
#   (eventos aleatorios: Bloque 8).
#
# Campos disponibles en las plantillas de falla: destino, lanzador, recurso,
# unidad, valor, minimo, optimo, dv_requerido_m_s, dv_disponible_m_s,
# consumo_w, generada_w. Para "presupuesto_excedido": costo_musd y
# presupuesto_musd. Un campo desconocido se deja tal cual (no rompe el juego).

ARCHIVO_MENSAJES = "mensajes.json"

FALLA_A_MENSAJE = {"no_llega": "delta_v_insuficiente", "se_apaga": "potencia_insuficiente"}

# Respaldo por si mensajes.json no trae estas claves. Desde el 15 nov ya están copiadas
# en mensajes.json (Justin puede mejorar ese texto; si existen allí, se usa el de allá
# y este respaldo se ignora).
MENSAJES_RESPALDO = {
    "explota": "The ship broke apart during launch: its structure is {valor} {unidad} and it needs at least {minimo} {unidad} to survive the vibration. The structure is the frame that holds everything together. Try giving more budget to the structure.",
    "incomunicada": "The mission stopped: your link sends only {valor} {unidad} and it needs at least {minimo} {unidad} to reach Earth. A weak antenna cannot send data from far away. Try investing more in communications.",
    "sin_ciencia": "The mission stopped: your instruments reach {valor} {unidad} and the goal needs at least {minimo}. Arriving is not enough if the science does not work. Try investing more in instruments.",
    "fuera_de_tiempo": "The mission stopped: the ship can work only {valor} {unidad} and it needs at least {minimo}. Autonomy limits how long a mission can last. Try investing more in mission time.",
}
MENSAJE_GENERICO = "The mission could not be completed. Try a different budget split."

# Unidades que en los datos están en español: en los mensajes (en inglés) se muestran así.
UNIDADES_EN = {"dias": "days", "puntos": "points"}
# Lo mismo con los destinos (en los datos están en español).
DESTINOS_EN = {"LEO": "LEO", "órbita lunar": "lunar orbit", "órbita de Marte": "Mars orbit",
               "superficie de Marte": "the surface of Mars"}


class _Campos(dict):
    """Deja sin cambiar los campos {desconocidos} en vez de lanzar un error."""
    def __missing__(self, clave):
        return "{" + clave + "}"


def _num(x):
    """Número para mostrar: entero si lo es (296.0 -> '296'), si no un decimal."""
    return str(int(round(x))) if abs(x - round(x)) < 0.05 else f"{x:.1f}"


def cargar_mensajes(ruta=None):
    """Lee datos/mensajes.json. Devuelve {} si el archivo no existe."""
    ruta = Path(ruta) if ruta else CARPETA_DATOS / ARCHIVO_MENSAJES
    if not ruta.exists():
        return {}
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def mensaje(clave, mensajes=None, **datos):
    """Texto de la plantilla 'clave' con los campos llenados. Busca primero en
    mensajes.json, luego en MENSAJES_RESPALDO. Nunca lanza error por falta de clave."""
    mensajes = mensajes if mensajes is not None else cargar_mensajes()
    plantilla = mensajes.get(clave) or MENSAJES_RESPALDO.get(clave) or MENSAJE_GENERICO
    return plantilla.format_map(_Campos(datos))


def mensajes_fallas(estado, mensajes=None):
    """Una entrada por CADA recurso que quedó bajo su mínimo, todas con el mismo peso:
    [{'clave': 'propulsion', 'falla': 'no_llega', 'mensaje': texto}, ...].
    Lista vacía si hubo éxito. Solo después de simular()."""
    if estado["fase"] != "resultado":
        raise ValueError("Primero hay que simular")
    mensajes = mensajes if mensajes is not None else cargar_mensajes()
    salida = []
    for clave in estado["resultado"]["bajo_minimo"]:
        r = _buscar_recurso(estado, clave)
        valor = valor_recurso(estado, clave)
        datos = {"destino": DESTINOS_EN.get(estado["destino"], estado["destino"]), "lanzador": estado["cohete"],
                 "recurso": clave, "unidad": UNIDADES_EN.get(r["unidad"], r["unidad"]),
                 "valor": _num(valor),
                 "minimo": _num(r["minimo"]), "optimo": _num(r["optimo"]),
                 "dv_requerido_m_s": _num(r["minimo"]), "dv_disponible_m_s": _num(valor),
                 "consumo_w": _num(r["minimo"]), "generada_w": _num(valor)}
        salida.append({"clave": clave, "falla": r["falla"],
                       "mensaje": mensaje(FALLA_A_MENSAJE.get(r["falla"], r["falla"]),
                                          mensajes, **datos)})
    return salida


def mensaje_resultado(estado, mensajes=None):
    """Texto explicativo del resultado (lo usa revelar). Solo después de simular().
    Éxito: el mensaje "exito". Falla: los mensajes de TODAS las fallas, uno por
    párrafo, en el orden del JSON (para mostrarlos por separado, usar mensajes_fallas)."""
    if estado["fase"] != "resultado":
        raise ValueError("Primero hay que simular")
    mensajes = mensajes if mensajes is not None else cargar_mensajes()
    if estado["resultado"]["exito"]:
        return mensaje("exito", mensajes, destino=DESTINOS_EN.get(estado["destino"], estado["destino"]),
                       lanzador=estado["cohete"])
    return "\n\n".join(f["mensaje"] for f in mensajes_fallas(estado, mensajes))


def mensaje_presupuesto(estado, mensajes=None):
    """Texto de 'presupuesto_excedido' con el gasto y el presupuesto actuales."""
    return mensaje("presupuesto_excedido", mensajes,
                   costo_musd=_num(gasto_total(estado)),
                   presupuesto_musd=_num(estado["presupuesto_musd"]))


# ---------------------------------------------------------------------------
# Fase 3: puntaje y revelado
# ---------------------------------------------------------------------------

def puntos_recurso(valor, optimo):
    """100 * (1 - |valor - óptimo| / óptimo), con 0 como mínimo."""
    return max(0.0, 100 * (1 - abs(valor - optimo) / optimo))


# Bonus por ahorro (decisión del equipo): si la misión se completa, el dinero que
# NO se gastó suma hasta BONUS_AHORRO_MAX puntos (proporcional a ahorro / presupuesto).
# Es un bonus SUMADO a la cercanía al óptimo (no ponderado): con la regla ponderada
# 0.85·cercanía + 15·ahorro el mejor puntaje bajaba a 74-77 y las 4-5 estrellas eran imposibles.
# Si la misión falla, el puntaje es 0: quedarse corto para "ahorrar" nunca conviene.
BONUS_AHORRO_MAX = 15


def ahorro(estado):
    """M USD que quedaron sin gastar (0 si se pasó del presupuesto)."""
    return max(0.0, presupuesto_restante(estado))


def puntaje_cercania(estado):
    """Promedio de los puntos por recurso (cercanía al óptimo), sin bonus. Float."""
    pts = [puntos_recurso(valor_recurso(estado, r["clave"]), r["optimo"])
           for r in estado["recursos"]]
    return sum(pts) / len(pts)


def puntaje(estado):
    """Puntaje final (entero 0-100): cercanía al óptimo + bonus por ahorro, con tope 100.
    0 si la misión falló."""
    if estado["fase"] != "resultado":
        raise ValueError("Primero hay que simular")
    if not estado["resultado"]["exito"]:
        return 0
    bonus = BONUS_AHORRO_MAX * ahorro(estado) / estado["presupuesto_musd"]
    return min(100, round(puntaje_cercania(estado) + bonus))


# Estrellas (0 a 5): 0 = falló · 1 = completó (cualquier puntaje) · 2, 3, 4 y 5 cuando el
# puntaje llega a cada valor de ESTRELLAS_UMBRALES · también 5 si el diseño es "óptimo"
# (todos los recursos a ±10 % de su óptimo). Cada misión puede traer su propio
# "estrellas": [dos, tres, cuatro, cinco] en parametros_misiones.json.
# Por qué estos valores (medido con los 5 niveles): cumplir justo los mínimos da 66-71
# puntos (1 estrella) y el mejor puntaje posible es 87-94, así que 5 estrellas (86) exige un
# reparto muy cuidado pero alcanzable. La propuesta 40/60/80 daba 2 estrellas solo por
# completar y dejaba 4-5 casi imposibles.
ESTRELLAS_UMBRALES = (72, 78, 82, 86)
ESTRELLAS_MAX = 5


def _umbrales_validos(e):
    if not (isinstance(e, (list, tuple)) and len(e) == ESTRELLAS_MAX - 1):
        return False
    if not all(_es_numero_positivo(x) for x in e):
        return False
    for i in range(len(e) - 1):          # de menor a mayor, sin repetir
        if e[i] >= e[i + 1]:
            return False
    return e[-1] <= 100


def umbrales_estrellas(m):
    """(puntaje para 2, 3, 4 y 5 estrellas) de una misión."""
    e = m.get("estrellas")
    return tuple(e) if _umbrales_validos(e) else ESTRELLAS_UMBRALES


def estrellas_de(puntaje, umbrales=ESTRELLAS_UMBRALES, completada=True, optimo=False):
    """Estrellas (0 a 5). 0 si la misión no se completó; si se completó, mínimo 1.
    optimo=True (todos los recursos cerca del óptimo) da 5 directamente."""
    if not completada:
        return 0
    if optimo:
        return ESTRELLAS_MAX
    n = 1
    for umbral in umbrales:
        if puntaje >= umbral:
            n = n + 1
    return n


def es_optimo(estado):
    """True si la misión se completó y TODOS los recursos quedaron a ±MARGEN_OPTIMO del óptimo."""
    if estado["fase"] != "resultado" or not estado["resultado"]["exito"]:
        return False
    for r in estado["recursos"]:
        if abs(valor_recurso(estado, r["clave"]) - r["optimo"]) > MARGEN_OPTIMO * r["optimo"] + TOLERANCIA:
            return False
    return True


def estrellas(estado):
    """Estrellas (0 a 5) de la misión ya simulada."""
    if estado["fase"] != "resultado":
        raise ValueError("Primero hay que simular")
    umbrales = estado.get("umbrales_estrellas", ESTRELLAS_UMBRALES)
    return estrellas_de(puntaje(estado), umbrales, estado["resultado"]["exito"], es_optimo(estado))


def puntaje_maximo(parametros, intentos=15000, semilla=0):
    """Estimación (por abajo) del mejor puntaje posible con el presupuesto: compra
    los mínimos, reparte la holgura al azar y mejora moviendo dinero entre recursos.
    Cuenta solo la cercanía al óptimo (sin bonus por ahorro), así que el puntaje real
    máximo es igual o mayor. Sirve para comprobar que las 5 estrellas son alcanzables.
    Devuelve un entero."""
    par = preparar_parametros(parametros)
    rec = par["recursos"]
    rnd = random.Random(semilla)
    costos_min = [costo_de(r, r["minimo"]) for r in rec]
    holgura = par["presupuesto_musd"] - sum(costos_min)
    if holgura < 0 or len(rec) < 2:
        return 0

    def puntos(dinero):
        p = [puntos_recurso(convertir(r, d), r["optimo"]) for r, d in zip(rec, dinero)]
        return sum(p) / len(p)

    mejor, mejor_d = -1.0, None
    for _ in range(intentos):
        w = [rnd.expovariate(1) for _ in rec]
        t = sum(w)
        d = [c + holgura * x / t for c, x in zip(costos_min, w)]
        s = puntos(d)
        if s > mejor:
            mejor, mejor_d = s, d
    for _ in range(intentos * 2):
        i, j = rnd.sample(range(len(rec)), 2)
        delta = rnd.random() * holgura * 0.05
        if mejor_d[j] - delta < costos_min[j]:
            continue
        d = list(mejor_d)
        d[i] += delta
        d[j] -= delta
        s = puntos(d)
        if s > mejor:
            mejor, mejor_d = s, d
    return round(mejor)


def revelar(estado):
    """Datos para la pantalla de resultados: por recurso, lo elegido, el mínimo,
    el óptimo, sus puntos y si quedó bajo el mínimo / cerca del óptimo.
    Devuelve: {'puntaje', 'exito', 'optimo', 'falla', 'fallas', 'mensaje',
               'estrellas', 'siguiente_estrella_pts', 'ahorro_musd',
               'presupuesto_usado_pct', 'recursos': [...]}.
      'puntaje' -> cercanía al óptimo + bonus por ahorro (0 si falló)
      'fallas'  -> TODAS las fallas, con el mismo peso: lista de
                   {'clave', 'falla', 'mensaje'} (vacía si hubo éxito)
      'falla'   -> la primera falla o None (solo por compatibilidad; usar 'fallas')
      'mensaje' -> texto de mensajes.json: "exito", o el de todas las fallas juntas
      'estrellas' -> 0 a 5 (ver estrellas_de)
      'siguiente_estrella_pts' -> puntaje que falta alcanzar para la próxima estrella
                   (None si falló o ya tiene 5)
      'ahorro_musd' -> M USD sin gastar; 'presupuesto_usado_pct' -> % del presupuesto gastado
      En cada recurso, 'faltante_pct' -> cuánto le faltó para el mínimo, en %
                   (0 si no quedó bajo el mínimo)."""
    if estado["fase"] != "resultado":
        raise ValueError("Primero hay que simular")
    filas = []
    for r in estado["recursos"]:
        valor = valor_recurso(estado, r["clave"])
        filas.append({
            "clave": r["clave"], "unidad": r["unidad"], "valor": valor,
            "minimo": r["minimo"], "optimo": r["optimo"],
            "puntos": round(puntos_recurso(valor, r["optimo"])),
            "bajo_minimo": valor < r["minimo"] - TOLERANCIA,
            "cerca_optimo": abs(valor - r["optimo"]) <= MARGEN_OPTIMO * r["optimo"] + TOLERANCIA,
            "faltante_pct": max(0.0, (r["minimo"] - valor) / r["minimo"] * 100),
            "fuente": r.get("fuente", ""),
        })
    exito = estado["resultado"]["exito"]
    pts = puntaje(estado)
    umbrales = estado.get("umbrales_estrellas", ESTRELLAS_UMBRALES)
    n_estrellas = estrellas(estado)
    if exito and n_estrellas < ESTRELLAS_MAX:
        siguiente = umbrales[n_estrellas - 1]
    else:
        siguiente = None
    return {"puntaje": pts, "exito": exito,
            "optimo": es_optimo(estado),
            "falla": estado["resultado"]["falla"],
            "fallas": mensajes_fallas(estado),
            "mensaje": mensaje_resultado(estado),
            "estrellas": n_estrellas,
            "siguiente_estrella_pts": siguiente,
            "ahorro_musd": ahorro(estado),
            "presupuesto_usado_pct": gasto_total(estado) / estado["presupuesto_musd"] * 100,
            "recursos": filas}


# ---------------------------------------------------------------------------
# Verificación de parametros_misiones.json (para Chambi y para el juego)
# ---------------------------------------------------------------------------

def _es_numero_positivo(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x > 0


def _problemas_fisica(f):
    """Problemas del bloque "fisica" de un recurso (lista vacía si está bien)."""
    if not isinstance(f, dict):
        return ["'fisica' debe ser un diccionario"]
    tipo = f.get("tipo")
    if tipo == "propulsion":
        requeridos = ("isp_s", "m_seca_kg", "musd_por_kg_propelente")
    elif tipo == "potencia":
        requeridos = ("musd_por_m2", "eficiencia", "distancia_ua")
    else:
        return [f"fisica.tipo debe ser 'propulsion' o 'potencia' (hay {tipo!r})"]
    p = [f"fisica: falta '{campo}' (número mayor que 0)"
         for campo in requeridos if not _es_numero_positivo(f.get(campo))]
    if tipo == "potencia" and _es_numero_positivo(f.get("eficiencia")) and f["eficiencia"] > 1:
        p.append("fisica: 'eficiencia' debe ser una fracción entre 0 y 1")
    return p


def recursos_provisionales(m):
    """Claves de los recursos cuyo bloque "fisica" está marcado "provisional": true
    (números a la espera de Chambi)."""
    return [r["clave"] for r in m.get("recursos") or []
            if isinstance(r.get("fisica"), dict) and r["fisica"].get("provisional")]


def verificar_parametros(m):
    """Revisa los parámetros de UNA misión. Devuelve la lista de problemas
    (vacía si está completa y es coherente). Una misión solo es jugable si
    la lista está vacía."""
    m = preparar_parametros(m)          # aplica destinos.json (idempotente)
    p = []
    mid = m.get("mision", "?")
    for campo in ("mision", "destino", "cohete"):
        if not m.get(campo):
            p.append(f"{mid}: falta '{campo}'")
    if not _es_numero_positivo(m.get("presupuesto_musd")):
        p.append(f"{mid}: falta 'presupuesto_musd' (número mayor que 0)")
    recursos = m.get("recursos") or []
    if not recursos:
        p.append(f"{mid}: no hay recursos")
    costo_min = costo_opt = 0.0
    completos = True
    for r in recursos:
        c = r.get("clave", "?")
        f = r.get("fisica")
        # con bloque "fisica" la tasa lineal ya no se usa
        campos_num = ("minimo", "optimo") if f else ("minimo", "optimo", "musd_por_unidad")
        for campo in campos_num:
            if not _es_numero_positivo(r.get(campo)):
                p.append(f"{mid}/{c}: falta '{campo}' (número mayor que 0)")
                completos = False
        if f:
            probs = _problemas_fisica(f)
            p.extend(f"{mid}/{c}: {x}" for x in probs)
            if probs:
                completos = False
        for campo in ("unidad", "falla", "fuente"):
            if not r.get(campo):
                p.append(f"{mid}/{c}: falta '{campo}'")
        if r.get("falla") and r["falla"] not in FALLAS_VALIDAS:
            p.append(f"{mid}/{c}: 'falla' debe ser una de {FALLAS_VALIDAS}")
        if completos and r["minimo"] > r["optimo"]:
            p.append(f"{mid}/{c}: el mínimo ({r['minimo']}) supera al óptimo ({r['optimo']})")
        if completos:
            costo_min += costo_de(r, r["minimo"])
            costo_opt += costo_de(r, r["optimo"])
    if not m.get("pistas"):
        p.append(f"{mid}: faltan 'pistas'")
    if "estrellas" in m and not _umbrales_validos(m["estrellas"]):
        p.append(f"{mid}: 'estrellas' debe ser [puntaje_2, puntaje_3, puntaje_4, puntaje_5] de menor a mayor, <= 100")
    # Condición de validez: costo(mínimos) <= presupuesto < costo(óptimos)
    if completos and recursos and _es_numero_positivo(m.get("presupuesto_musd")):
        pres = m["presupuesto_musd"]
        if costo_min > pres + TOLERANCIA:
            p.append(f"{mid}: IMPOSIBLE: los mínimos cuestan {costo_min:.2f} M USD y el presupuesto es {pres}")
        if costo_opt <= pres:
            p.append(f"{mid}: SIN DECISIÓN: los óptimos cuestan {costo_opt:.2f} M USD y el presupuesto ({pres}) alcanza para todos")
    return p


def verificar_archivo(ruta=None):
    """Verifica todo parametros_misiones.json. Devuelve {id_mision: [problemas]}."""
    ruta = Path(ruta) if ruta else CARPETA_DATOS / ARCHIVO_PARAMETROS
    with open(ruta, encoding="utf-8") as f:
        return {m.get("mision", "?"): verificar_parametros(m) for m in json.load(f)}


def provisionales_archivo(ruta=None):
    """{id_mision: [claves provisionales]} de todo parametros_misiones.json."""
    ruta = Path(ruta) if ruta else CARPETA_DATOS / ARCHIVO_PARAMETROS
    with open(ruta, encoding="utf-8") as f:
        return {m.get("mision", "?"): recursos_provisionales(m) for m in json.load(f)}


def verificar_niveles(ruta=None):
    """Revisa que cada nivel de DIFICULTADES tenga EXACTAMENTE una misión en
    parametros_misiones.json (el campo "dificultad" es la asignación nivel -> misión).
    Avisa de: nivel sin misión, nivel con varias, nivel desconocido (se compara tal
    cual: "Hard", no "hard"), ids repetidos, y niveles que no incluyen los recursos
    del nivel anterior (cada nivel añade recursos, no quita). Devuelve la lista de
    problemas (vacía si todo está bien)."""
    ruta = Path(ruta) if ruta else CARPETA_DATOS / ARCHIVO_PARAMETROS
    with open(ruta, encoding="utf-8") as f:
        misiones = json.load(f)
    p, ids, por_nivel = [], set(), {}
    for m in misiones:
        mid = m.get("mision", "?")
        if mid in ids:
            p.append(f"id repetido: '{mid}'")
        ids.add(mid)
        nivel = m.get("dificultad")
        if nivel not in DIFICULTADES:
            p.append(f"{mid}: nivel desconocido {nivel!r}; debe ser uno de {DIFICULTADES}")
            continue
        por_nivel.setdefault(nivel, []).append(m)
    for nivel in DIFICULTADES:
        ms = por_nivel.get(nivel, [])
        if not ms:
            p.append(f"nivel {nivel}: no tiene misión asignada")
        elif len(ms) > 1:
            p.append(f"nivel {nivel}: tiene {len(ms)} misiones {[m.get('mision') for m in ms]}; debe tener una sola")
    anterior = None                      # (nivel, claves de recursos) del nivel anterior
    for nivel in DIFICULTADES:
        ms = por_nivel.get(nivel, [])
        if len(ms) != 1:
            anterior = None
            continue
        claves = {r.get("clave") for r in ms[0].get("recursos") or []}
        if anterior and not anterior[1] <= claves:
            p.append(f"nivel {nivel}: le faltan recursos del nivel {anterior[0]}: {sorted(anterior[1] - claves)}")
        anterior = (nivel, claves)
    return p


# ---------------------------------------------------------------------------
# Validación: ¿la misión tiene solución? (sección 7.2 del bosquejo)
# ---------------------------------------------------------------------------

def validar_mision(parametros, pasos=10):
    """Prueba repartos en escalones de presupuesto/pasos y cuenta cuántos
    completan la misión, cuántos quedan 'óptimos' y el mejor puntaje.
    Criterio: la mayoría NO completa, algunos sí, y el mejor puntaje es alto."""
    n = len(parametros["recursos"])
    claves = [r["clave"] for r in parametros["recursos"]]
    paso = parametros["presupuesto_musd"] / pasos
    total = completan = optimos = 0
    mejor = 0
    for combo in itertools.product(range(pasos + 1), repeat=n):
        if sum(combo) > pasos:               # se pasa del presupuesto
            continue
        e = iniciar_mision(parametros)
        for clave, k in zip(claves, combo):
            repartir(e, clave, k * paso)
        revisar(e)
        simular(e)
        total += 1
        if e["resultado"]["exito"]:
            completan += 1
            info = revelar(e)
            optimos += info["optimo"]
            mejor = max(mejor, info["puntaje"])
    return {"repartos": total, "completan": completan,
            "optimos": optimos, "mejor_puntaje": mejor}


# Validación fina (añadida por la interfaz, 15 nov): más precisa que validar_mision.
# Parte de los COSTOS DE LOS MÍNIMOS y reparte el sobrante (presupuesto − Σ mínimos) en
# pasos pequeños, incluyendo dejar dinero sin gastar (para el bonus por ahorro).
# Truco para que sea rápida: los puntos de cada recurso se calculan una sola vez por
# escalón (tabla), y cada reparto solo suma valores de esas tablas.

PASOS_FINOS = {1: 200, 2: 200, 3: 100, 4: 60, 5: 30, 6: 20}   # escalones del sobrante según nº de recursos
MARGEN_SOBRANTE_MIN = 0.10    # "margen razonable": el sobrante es al menos el 10 % del presupuesto


def _composiciones(n, total):
    """Todas las listas de n enteros >= 0 cuya suma es <= total."""
    if n == 0:
        yield []
        return
    for k in range(total + 1):
        for resto in _composiciones(n - 1, total - k):
            yield [k] + resto


def validar_mision_fina(parametros, pasos=None):
    """Busca el mejor reparto posible repartiendo el sobrante en escalones finos y lo
    confirma jugándolo con las funciones reales (iniciar_mision -> ... -> revelar).
    Devuelve un diccionario con: presupuesto, suma_minimos, suma_optimos, sobrante_musd,
    sobrante_pct, tradeoff (Σmín <= P < Σópt), completable, repartos_probados,
    mejor_puntaje, mejor_estrellas, mejor_reparto ({clave: M USD}), mejor_valores
    ({clave: cantidad}), pct_5_estrellas (de los repartos probados), margen_ok y sugerencia
    (texto o None, si el margen no es razonable)."""
    par = preparar_parametros(parametros)
    rec = par["recursos"]
    claves = [r["clave"] for r in rec]
    pres = par["presupuesto_musd"]
    n = len(rec)
    if pasos is None:
        pasos = PASOS_FINOS.get(n, 20)
    costos_min = [costo_de(r, r["minimo"]) for r in rec]
    costos_opt = [costo_de(r, r["optimo"]) for r in rec]
    suma_min, suma_opt = sum(costos_min), sum(costos_opt)
    sobrante = pres - suma_min
    salida = {"mision": par["mision"], "presupuesto": pres, "suma_minimos": suma_min,
              "suma_optimos": suma_opt, "sobrante_musd": sobrante,
              "sobrante_pct": 100 * sobrante / pres, "tradeoff": suma_min <= pres < suma_opt,
              "recursos": n, "pasos": pasos}
    if sobrante < 0:
        salida.update(completable=False, margen_ok=False,
                      sugerencia=f"subir presupuesto_musd a {suma_min / (1 - MARGEN_SOBRANTE_MIN):.2f} M USD")
        return salida

    # Tabla de puntos por recurso y escalón. Cada mínimo lleva un margen fijo EPS (para no
    # caer bajo él por redondeo de decimales) que se descuenta del sobrante, así ningún
    # reparto se pasa del presupuesto.
    EPS = 1e-6
    paso = (sobrante - 2 * n * EPS) / pasos
    tablas = []
    for r, c in zip(rec, costos_min):
        fila = []
        for k in range(pasos + 1):
            fila.append(puntos_recurso(convertir(r, c + EPS + k * paso), r["optimo"]))
        tablas.append(fila)

    umbrales = umbrales_estrellas(par)
    mejor, mejor_combo, probados, con_cinco = -1, None, 0, 0
    for combo in _composiciones(n, pasos):
        probados += 1
        cercania = sum(tablas[i][combo[i]] for i in range(n)) / n
        ahorro_musd = pres - suma_min - n * EPS - sum(combo) * paso
        pts = min(100, round(cercania + BONUS_AHORRO_MAX * ahorro_musd / pres))
        if pts >= umbrales[-1]:
            con_cinco += 1
        if pts > mejor:
            mejor, mejor_combo = pts, combo

    # Confirmación con las funciones reales del juego
    reparto = {c: costos_min[i] + EPS + mejor_combo[i] * paso for i, c in enumerate(claves)}
    e = iniciar_mision(parametros)
    for c, d in reparto.items():
        repartir(e, c, d)
    assert revisar(e)["ok"], "el mejor reparto no entra en el presupuesto"
    assert simular(e)["exito"], "el mejor reparto no completa la misión"
    info = revelar(e)
    salida.update(completable=True, repartos_probados=probados, mejor_puntaje=info["puntaje"],
                  mejor_estrellas=info["estrellas"], mejor_reparto=reparto,
                  mejor_valores={f["clave"]: f["valor"] for f in info["recursos"]},
                  pct_5_estrellas=100 * con_cinco / probados)
    salida["margen_ok"] = (salida["sobrante_pct"] >= 100 * MARGEN_SOBRANTE_MIN
                           and info["estrellas"] == ESTRELLAS_MAX and salida["tradeoff"])
    sugerencia = None
    if not salida["margen_ok"]:
        partes = []
        if salida["sobrante_pct"] < 100 * MARGEN_SOBRANTE_MIN:
            partes.append(f"subir presupuesto_musd de {pres} a {suma_min / (1 - MARGEN_SOBRANTE_MIN):.2f} M USD "
                          f"(sobrante del 10 %)")
        if not salida["tradeoff"]:
            partes.append(f"bajar presupuesto_musd por debajo de Σ óptimos = {suma_opt:.2f} M USD")
        if info["estrellas"] < ESTRELLAS_MAX:
            partes.append("las 5 estrellas no son alcanzables: revisar presupuesto u óptimos")
        sugerencia = "; ".join(partes)
    salida["sugerencia"] = sugerencia
    return salida


# ---------------------------------------------------------------------------
# Parrilla de misiones y progreso  (BLOQUE 2)
# ---------------------------------------------------------------------------
# La parrilla se arma con parametros_misiones.json (misiones.json ya no se usa).
# Cada misión de ese archivo trae al menos "mision" (el id), "dificultad",
# "destino" y "cohete"; "nombre" es opcional (si falta, se arma a partir del id).
# Una misión es JUGABLE si sus parámetros están completos y son válidos
# (verificar_parametros); si no, se muestra como "próximamente".

DIFICULTADES = ["Easy", "Normal", "Hard", "Harder", "Insane"]   # orden de la parrilla
DESBLOQUEO_EN_ORDEN = True    # Justin decide; False = todas abiertas desde el inicio


def nuevo_progreso():
    """Progreso de un jugador nuevo:
    {'completadas': {id_mision: mejor_puntaje}, 'estrellas': {id_mision: mejores_estrellas}}.
    Vive en memoria (así también funciona en la versión web con pygbag)."""
    return {"completadas": {}, "estrellas": {}}


def _nombre_mision(m):
    """Nombre para mostrar: el campo "nombre" si existe; si no, se arma con el id
    ("normal_leo" -> "Normal Leo")."""
    return m.get("nombre") or m["mision"].replace("_", " ").title()


def cargar_misiones(progreso=None, ruta_parametros=None):
    """Lista para la parrilla, ordenada por nivel. Sale de parametros_misiones.json:
    cada nivel de DIFICULTADES tiene UNA misión (la asignación es el campo
    "dificultad"). Una misión con nivel desconocido, o la segunda de un nivel ya
    ocupado, no aparece (verificar_niveles lo avisa). Cada elemento trae SOLO estos
    campos (nunca mínimos ni óptimos):
      'id', 'nombre', 'nivel' (1 a 5), 'dificultad', 'destino', 'cohete',
      'presupuesto_musd', 'estado', 'mejor_puntaje' (None si no está completada) y
      'estrellas' (0 si no está completada; si lo está, 1 a 5: las mejores logradas).
    'estado' es una de:
      'completada'    -> ya se completó (se puede repetir)
      'disponible'    -> se puede jugar
      'bloqueada'     -> hay que completar la anterior (si DESBLOQUEO_EN_ORDEN)
      'proximamente'  -> sus parámetros aún están incompletos o no son válidos
    Una misión 'proximamente' no cuenta para el desbloqueo en orden: la
    siguiente se abre al completar la última misión jugable anterior."""
    progreso = progreso if progreso is not None else nuevo_progreso()
    ruta = Path(ruta_parametros) if ruta_parametros else CARPETA_DATOS / ARCHIVO_PARAMETROS
    with open(ruta, encoding="utf-8") as f:
        misiones = json.load(f)
    orden = {d: i for i, d in enumerate(DIFICULTADES)}
    misiones = sorted((m for m in misiones if m.get("dificultad") in orden),
                      key=lambda m: orden[m["dificultad"]])

    parrilla = []
    anterior_completada = True              # la primera misión siempre está abierta
    ocupados = set()
    for m in misiones:
        nivel = m["dificultad"]
        if nivel in ocupados:               # segunda misión del mismo nivel: se ignora
            continue
        ocupados.add(nivel)
        mid = m["mision"]
        completada = mid in progreso["completadas"]
        mejor = progreso["completadas"].get(mid)
        fila = {"id": mid, "nombre": _nombre_mision(m), "nivel": orden[nivel] + 1,
                "dificultad": nivel, "destino": m.get("destino"), "cohete": m.get("cohete"),
                "presupuesto_musd": m.get("presupuesto_musd"), "mejor_puntaje": mejor,
                "estrellas": 0}
        if completada:
            # Mejores estrellas guardadas; si el progreso es antiguo (sin 'estrellas'),
            # se calculan con el mejor puntaje.
            guardadas = progreso.get("estrellas", {}).get(mid)
            if guardadas is None:
                guardadas = estrellas_de(mejor, umbrales_estrellas(m))
            fila["estrellas"] = guardadas
        if completada:
            fila["estado"] = "completada"
        elif verificar_parametros(m):       # lista de problemas no vacía
            fila["estado"] = "proximamente"
        elif DESBLOQUEO_EN_ORDEN and not anterior_completada:
            fila["estado"] = "bloqueada"
        else:
            fila["estado"] = "disponible"
        if fila["estado"] != "proximamente":
            anterior_completada = completada
        parrilla.append(fila)
    return parrilla


def puede_jugar(progreso, mision_id, ruta_parametros=None):
    """True si la misión está 'disponible' o 'completada' (repetirla)."""
    for fila in cargar_misiones(progreso, ruta_parametros):
        if fila["id"] == mision_id:
            return fila["estado"] in ("disponible", "completada")
    raise ValueError(f"Misión desconocida: '{mision_id}'")


def registrar_resultado(progreso, estado):
    """Llamar después de simular(). Si la misión se completó, la marca y guarda
    el mejor puntaje. Devuelve el progreso."""
    if estado["fase"] != "resultado":
        raise ValueError("Primero hay que simular")
    if estado["resultado"]["exito"]:
        mid = estado["mision"]
        pts = puntaje(estado)
        progreso["completadas"][mid] = max(pts, progreso["completadas"].get(mid, 0))
        if "estrellas" not in progreso:
            progreso["estrellas"] = {}
        progreso["estrellas"][mid] = max(estrellas(estado), progreso["estrellas"].get(mid, 0))
    return progreso


# ---------------------------------------------------------------------------
# Pruebas  (VALORES FICTICIOS: solo sirven para probar el código;
# los reales los entrega Chambi en parametros_misiones.json)
# ---------------------------------------------------------------------------

MISION_PRUEBA = {
    "mision": "prueba", "destino": "LEO", "cohete": "Electron",
    "presupuesto_musd": 7,
    "pistas": ["pista de prueba"],
    "recursos": [
        {"clave": "estructura", "unidad": "kg", "minimo": 20, "optimo": 30,
         "musd_por_unidad": 0.1, "falla": "explota", "fuente": "prueba"},
        {"clave": "propulsion", "unidad": "m/s", "minimo": 1000, "optimo": 1200,
         "musd_por_unidad": 0.004, "falla": "no_llega", "fuente": "prueba"},
    ],
}
# Costo del mínimo: 20*0.1 + 1000*0.004 = 2 + 4 = 6 M USD
# Costo del óptimo: 30*0.1 + 1200*0.004 = 3 + 4.8 = 7.8 M USD  (presupuesto 7: entre 6 y 7.8)


def _mision_lista(estructura_musd, propulsion_musd):
    e = iniciar_mision(MISION_PRUEBA)
    repartir(e, "estructura", estructura_musd)
    repartir(e, "propulsion", propulsion_musd)
    return e


if __name__ == "__main__":
    import sys
    if "--validar-fino" in sys.argv:     # python nucleo.py --validar-fino
        print(f"{'misión':<20}{'P':>7}{'Σmín':>8}{'Σópt':>8}{'sobra':>8}{'repartos':>10}{'mejor':>7}{'★':>3}{'%5★':>7}  margen")
        for mid in [f["id"] for f in cargar_misiones()]:
            r = validar_mision_fina(cargar_parametros(mid))
            print(f"{mid:<20}{r['presupuesto']:>7}{r['suma_minimos']:>8.2f}{r['suma_optimos']:>8.2f}"
                  f"{r['sobrante_pct']:>7.1f}%{r.get('repartos_probados', 0):>10}{r.get('mejor_puntaje', 0):>7}"
                  f"{r.get('mejor_estrellas', 0):>3}{r.get('pct_5_estrellas', 0):>6.1f}%  "
                  f"{'OK' if r['margen_ok'] else 'AJUSTAR: ' + r['sugerencia']}")
            if r.get("completable"):
                print("   mejor reparto:", {c: round(v, 2) for c, v in r["mejor_reparto"].items()}, "M USD")
                print("   cantidades:  ", {c: round(v, 1) for c, v in r["mejor_valores"].items()})
        sys.exit()

    if "--verificar" in sys.argv:        # python nucleo.py --verificar [ruta.json]
        ruta = sys.argv[sys.argv.index("--verificar") + 1:][:1]
        prov = provisionales_archivo(ruta[0] if ruta else None)
        for mid, problemas in verificar_archivo(ruta[0] if ruta else None).items():
            print(f"[{'OK ' if not problemas else 'PENDIENTE'}] {mid}")
            for x in problemas:
                print("   -", x)
            if prov.get(mid):
                print("   * valores PROVISIONALES (esperan a Chambi):", ", ".join(prov[mid]))
        probs_niveles = verificar_niveles(ruta[0] if ruta else None)
        print(f"[{'OK ' if not probs_niveles else 'PENDIENTE'}] niveles {DIFICULTADES}")
        for x in probs_niveles:
            print("   -", x)
        sys.exit()

    # 1. Reparto dentro del presupuesto y sobre los mínimos -> éxito
    e = _mision_lista(2.5, 4.5)
    assert revisar(e)["ok"]
    assert simular(e)["exito"]
    print("OK  éxito            -> puntaje", puntaje(e))

    # 2. Reparto en el óptimo exacto -> 100 puntos y 'óptimo'
    e = _mision_lista(3.0, 4.8)
    e["presupuesto_musd"] = 10      # solo para esta prueba: el óptimo exacto no cabe en 7
    revisar(e); simular(e)
    info = revelar(e)
    assert info["puntaje"] == 100 and info["optimo"]
    print("OK  óptimo exacto    -> puntaje", info["puntaje"])

    # 3. Propulsión bajo el mínimo -> 'no_llega' y puntaje 0
    e = _mision_lista(3.0, 3.0)
    revisar(e)
    r = simular(e)
    assert not r["exito"] and r["falla"] == "no_llega" and puntaje(e) == 0
    print("OK  falla propulsión ->", r["falla"])

    # 4. Si fallan dos, se muestra la primera de la lista (estructura -> explota)
    e = _mision_lista(1.0, 1.0)
    revisar(e)
    r = simular(e)
    assert r["falla"] == "explota" and r["bajo_minimo"] == ["estructura", "propulsion"] and r["fallas"] == ["explota", "no_llega"]
    print("OK  dos fallas       ->", r["falla"], r["bajo_minimo"])

    # 5. Pasarse del presupuesto: la revisión lo detecta y no deja simular
    e = _mision_lista(6.0, 6.0)
    rev = revisar(e)
    assert not rev["ok"] and abs(rev["exceso_musd"] - 5.0) < 1e-9
    try:
        simular(e)
        raise AssertionError("debió fallar")
    except ValueError:
        pass
    print("OK  presupuesto      -> exceso", rev["exceso_musd"], "M USD")

    # 6. Lo visible durante el reparto no trae mínimos ni óptimos
    e = _mision_lista(2.0, 4.0)
    for fila in recursos_visibles(e):
        assert "minimo" not in fila and "optimo" not in fila
    assert abs(presupuesto_restante(e) - 1.0) < 1e-9
    print("OK  vista oculta     -> restante", presupuesto_restante(e))

    # 7. Validación de solución de la misión de prueba
    print("Validación:", validar_mision(MISION_PRUEBA))

    # ---- Bloque 4: física real en convertir ----
    import math
    # 8. Caso conocido de fisica.py: 3100 m/s, 320 s, 500 kg -> ~843 kg de propelente
    prop = {"clave": "propulsion", "fisica": {"tipo": "propulsion", "isp_s": 320,
            "m_seca_kg": 500, "musd_por_kg_propelente": 0.01}}
    kg = fisica.masa_propelente(3100, 320, 500)
    assert abs(kg - 843) < 1
    assert math.isclose(convertir(prop, kg * 0.01), 3100, rel_tol=1e-9)
    assert convertir(prop, 0.0) == 0.0                      # sin dinero no hay delta-v
    assert math.isclose(costo_de(prop, 3100), kg * 0.01, rel_tol=1e-9)   # inversa
    print(f"OK  propulsión física -> {kg:.1f} kg de propelente dan {convertir(prop, kg * 0.01):.0f} m/s")

    # 9. Potencia: 2 m2 al 28 % -> 762.16 W a 1 UA y 328.14 W a 1.524 UA (casos de potencia_costo.py)
    for dist, esperado in ((1.0, 762.16), (1.524, 328.14)):
        pot = {"clave": "potencia", "fisica": {"tipo": "potencia", "musd_por_m2": 1.0,
               "eficiencia": 0.28, "distancia_ua": dist}}
        assert math.isclose(convertir(pot, 2.0), esperado, rel_tol=1e-3)
        assert math.isclose(costo_de(pot, esperado), 2.0, rel_tol=1e-3)
    print("OK  potencia física   -> 762.2 W a 1 UA, 328.1 W a 1.524 UA")

    # 10. delta_v_nave sale de destinos.json (LEO = 0: ahí el mínimo queda en el JSON)
    assert [delta_v_nave(d) for d in ("LEO", "órbita lunar", "órbita de Marte", "superficie de Marte")] \
        == [0, 4000, 5000, 9100]
    print("OK  delta_v_nave      -> LEO 0, Luna 4000, Marte 5000, superficie 9100 m/s")

    # 11. preparar_parametros pone mínimo y distancia desde destinos.json
    marte = {"mision": "x", "destino": "órbita de Marte", "cohete": "?", "presupuesto_musd": 1,
             "pistas": ["p"], "recursos": [
                 dict(prop, minimo=1, optimo=2, unidad="m/s", falla="no_llega", fuente="p"),
                 {"clave": "potencia", "minimo": 1, "optimo": 2, "unidad": "W", "falla": "se_apaga",
                  "fuente": "p", "fisica": {"tipo": "potencia", "musd_por_m2": 1, "eficiencia": 0.28,
                                            "distancia_ua": 99}}]}
    prep = preparar_parametros(marte)
    assert prep["recursos"][0]["minimo"] == 5000 and prep["recursos"][1]["fisica"]["distancia_ua"] == 1.524
    assert marte["recursos"][0]["minimo"] == 1            # no modifica la original
    print("OK  destinos.json     -> mínimo de propulsión 5000 m/s, distancia 1.524 UA")

    # 12. Easy y Normal reales (con física) son jugables y válidos
    for mid in ("easy_cubesat", "normal_leo"):
        par = cargar_parametros(mid)
        assert verificar_parametros(par) == [], verificar_parametros(par)
        assert any(r.get("fisica") for r in par["recursos"])
        print(f"OK  {mid:<17}-> válida con física; validación:", validar_mision(par))

    # ---- Bloque 6: mensajes y revelado ----
    easy = cargar_parametros("easy_cubesat")
    normal = cargar_parametros("normal_leo")

    def jugar(par, **reparto):
        e = iniciar_mision(par)
        for k, v in reparto.items():
            repartir(e, k, v)
        revisar(e); simular(e)
        return revelar(e)

    # 13. Éxito: el mensaje nombra el destino y no queda ninguna plantilla sin llenar
    info = jugar(easy, estructura=8.5, propulsion=6.0)
    assert info["exito"] and info["falla"] is None
    assert "LEO" in info["mensaje"] and "{" not in info["mensaje"]
    print("OK  mensaje éxito     ->", info["mensaje"][:45] + "...")

    # 14. no_llega -> delta_v_insuficiente, con el mínimo y lo que logró la nave
    info = jugar(easy, estructura=8.5, propulsion=3.0)
    logrado = _num(info["recursos"][1]["valor"])
    assert info["falla"] == "no_llega" and "{" not in info["mensaje"]
    assert "250 m/s" in info["mensaje"] and f"{logrado} m/s" in info["mensaje"]
    print("OK  mensaje no_llega  -> pide 250 m/s, la nave tiene", logrado, "m/s")

    # 15. se_apaga -> potencia_insuficiente (Normal)
    info = jugar(normal, estructura=14.0, propulsion=17.0, potencia=5.0)
    assert info["falla"] == "se_apaga" and "{" not in info["mensaje"] and "350 W" in info["mensaje"]
    print("OK  mensaje se_apaga  -> pide 350 W")

    # 16. explota -> mensaje completo (de mensajes.json o del respaldo)
    info = jugar(easy, estructura=3.0, propulsion=6.0)
    assert info["falla"] == "explota" and "{" not in info["mensaje"] and "6 kg" in info["mensaje"]
    print("OK  mensaje explota   ->", info["mensaje"][:45] + "...")

    # 17. Cada falla (también las de Harder e Insane) tiene mensaje completo
    for falla in FALLAS_VALIDAS:
        txt = mensaje(FALLA_A_MENSAJE.get(falla, falla), recurso="x", unidad="u", valor=1,
                      minimo=2, optimo=3, dv_requerido_m_s=2, dv_disponible_m_s=1,
                      consumo_w=2, generada_w=1)
        assert txt != MENSAJE_GENERICO and "{" not in txt, falla
    print("OK  todas las fallas  -> tienen mensaje:", FALLAS_VALIDAS)

    # 17b. Las unidades en español de los datos salen en inglés en los mensajes
    arte = cargar_parametros("insane_artemis1")
    e = iniciar_mision(arte)
    for r in preparar_parametros(arte)["recursos"]:
        repartir(e, r["clave"], costo_de(r, r["minimo"]) * (0.5 if r["clave"] in ("datos", "tiempo") else 1.01))
    revisar(e); simular(e)
    textos_fallas = " ".join(f["mensaje"] for f in mensajes_fallas(e))
    assert "days" in textos_fallas and "points" in textos_fallas, textos_fallas
    assert " dias" not in textos_fallas and " puntos" not in textos_fallas
    print("OK  unidades en inglés -> days, points")
    e = iniciar_mision(arte)
    for r in preparar_parametros(arte)["recursos"]:
        repartir(e, r["clave"], costo_de(r, r["minimo"]) * 1.01)
    revisar(e); simular(e)
    assert "lunar orbit" in mensaje_resultado(e) and "órbita" not in mensaje_resultado(e)
    print("OK  destinos en inglés -> lunar orbit")

    # 18. Presupuesto excedido: revisar trae el mensaje con el gasto y el presupuesto
    e = iniciar_mision(easy)
    repartir(e, "estructura", 10.0); repartir(e, "propulsion", 10.0)
    rev = revisar(e)
    assert not rev["ok"] and "20" in rev["mensaje"] and "14.5" in rev["mensaje"] and "{" not in rev["mensaje"]
    e = iniciar_mision(easy)
    repartir(e, "estructura", 8.5); repartir(e, "propulsion", 6.0)
    assert revisar(e)["mensaje"] is None
    print("OK  presupuesto       ->", rev["mensaje"][:45] + "...")

    # ---- Todas las fallas, niveles y estrellas ----
    import tempfile
    IDS_NIVELES = ["easy_cubesat", "normal_leo", "hard_mro_marte", "harder_perseverance", "insane_artemis1"]

    # 19. Si fallan varios recursos se muestran TODOS, con el mismo peso
    e = iniciar_mision(easy)
    repartir(e, "estructura", 3.0); repartir(e, "propulsion", 3.0)
    revisar(e)
    r = simular(e)
    assert r["fallas"] == ["explota", "no_llega"] and r["falla"] == "explota"
    info = revelar(e)
    assert [f["clave"] for f in info["fallas"]] == ["estructura", "propulsion"]
    assert [f["falla"] for f in info["fallas"]] == ["explota", "no_llega"]
    assert "broke apart" in info["mensaje"] and "250 m/s" in info["mensaje"] and "{" not in info["mensaje"]
    assert info["estrellas"] == 0 and info["siguiente_estrella_pts"] is None
    print("OK  varias fallas     ->", [f["falla"] for f in info["fallas"]])

    # 20. Los 5 niveles: cada uno con su misión y todas jugables (ya con las 6 fallas)
    assert verificar_niveles() == [], verificar_niveles()
    assert all(v == [] for v in verificar_archivo().values()), verificar_archivo()
    parrilla = cargar_misiones()
    assert [f["dificultad"] for f in parrilla] == DIFICULTADES and [f["nivel"] for f in parrilla] == [1, 2, 3, 4, 5]
    assert [f["id"] for f in parrilla] == IDS_NIVELES
    assert [f["estado"] for f in parrilla] == ["disponible"] + ["bloqueada"] * 4
    assert all(f["estrellas"] == 0 for f in parrilla)
    print("OK  5 niveles         ->", [(f["nivel"], f["id"]) for f in parrilla])

    # 21. verificar_niveles detecta nivel faltante, repetido, desconocido y recursos que faltan
    def con_niveles(lista):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "p.json"
            ruta.write_text(json.dumps(lista), encoding="utf-8")
            return verificar_niveles(ruta)

    def mis(mid, nivel, *claves):
        return {"mision": mid, "dificultad": nivel, "recursos": [{"clave": c} for c in claves]}

    completo = [mis("a", "Easy", "estructura"), mis("b", "Normal", "estructura", "potencia"),
                mis("c", "Hard", "estructura", "potencia"), mis("d", "Harder", "estructura", "potencia"),
                mis("e", "Insane", "estructura", "potencia")]
    assert con_niveles(completo) == []
    assert any("Insane" in x and "no tiene misión" in x for x in con_niveles(completo[:4]))
    assert any("Normal" in x and "2 misiones" in x for x in con_niveles(completo + [mis("f", "Normal", "estructura", "potencia")]))
    assert any("'hard'" in x for x in con_niveles(completo[:2] + [mis("c", "hard", "estructura")] + completo[3:]))
    assert any("repetido" in x for x in con_niveles(completo + [mis("a", "Easy", "estructura")]))
    sin_prop = [mis("a", "Easy", "estructura", "propulsion")] + completo[1:]
    assert any("Normal" in x and "propulsion" in x for x in con_niveles(sin_prop))
    print("OK  verificar_niveles -> detecta faltante, repetido, desconocido y recursos que faltan")

    # 22. Estrellas 0-5: 1 = completar, 2 >= 72, 3 >= 78, 4 >= 82, 5 >= 86 o diseño óptimo
    assert [estrellas_de(p) for p in (0, 71, 72, 77, 78, 81, 82, 85, 86, 100)] == [1, 1, 2, 2, 3, 3, 4, 4, 5, 5]
    assert estrellas_de(90, completada=False) == 0
    assert estrellas_de(50, optimo=True) == 5
    assert umbrales_estrellas({"estrellas": [60, 70, 80, 90]}) == (60, 70, 80, 90)
    assert umbrales_estrellas({"estrellas": [80, 60, 70, 90]}) == ESTRELLAS_UMBRALES   # inválido -> los de siempre
    assert umbrales_estrellas({"estrellas": [60, 80]}) == ESTRELLAS_UMBRALES           # formato viejo (0-3)
    assert umbrales_estrellas({}) == ESTRELLAS_UMBRALES
    assert verificar_parametros(dict(easy, estrellas=[80, 60, 70, 90])) != []
    assert verificar_parametros(dict(easy, estrellas=[60, 70, 80, 90])) == []

    # 23. revelar trae estrellas, cuánto falta para la siguiente, ahorro y % usado
    info = jugar(easy, estructura=6.0, propulsion=5.0)       # justo los mínimos: se aprueba, 1 estrella
    assert info["exito"] and info["estrellas"] == 1 and info["siguiente_estrella_pts"] == 72, info["puntaje"]
    assert abs(info["ahorro_musd"] - 3.5) < 1e-9 and abs(info["presupuesto_usado_pct"] - 11 / 14.5 * 100) < 1e-9
    info = jugar(easy, estructura=8.5, propulsion=6.0)       # todo el presupuesto, buen reparto
    assert info["puntaje"] == 87 and info["estrellas"] == 5 and info["siguiente_estrella_pts"] is None
    assert info["ahorro_musd"] == 0 and abs(info["presupuesto_usado_pct"] - 100) < 1e-9
    assert puntos_recurso(12.0, 8.5) < puntos_recurso(8.5, 8.5) == 100        # pasarse del óptimo resta
    print("OK  estrellas         -> mínimos 1, buen reparto 5")

    # 23b. Bonus por ahorro: con la misma cercanía, ahorrar suma; fallar sigue dando 0
    e = iniciar_mision(easy)
    repartir(e, "estructura", 6.0); repartir(e, "propulsion", 5.0)
    revisar(e); simular(e)
    assert puntaje(e) == round(puntaje_cercania(e) + 15 * 3.5 / 14.5) > round(puntaje_cercania(e))
    assert jugar(easy, estructura=3.0, propulsion=1.0)["puntaje"] == 0      # ahorró mucho pero falló
    assert estrellas(e) == revelar(e)["estrellas"]
    print("OK  bonus por ahorro  -> mínimos:", round(puntaje_cercania(e)), "+ bonus =", puntaje(e))

    # 23c. cotizar es la inversa de convertir y valida la entrada
    e = iniciar_mision(easy)
    assert math.isclose(cotizar(e, "estructura", 8.5), 8.5)                 # 1 M USD por kg
    costo = cotizar(e, "propulsion", 400)
    repartir(e, "propulsion", costo)
    assert math.isclose(valor_recurso(e, "propulsion"), 400, rel_tol=1e-9)
    assert cotizar(e, "propulsion", 0) == 0
    for malo in (("estructura", -1), ("antena", 5)):
        try:
            cotizar(e, *malo)
            raise AssertionError("debió fallar")
        except ValueError:
            pass
    assert math.isclose(repartir_valor(e, "estructura", 7.0), 7.0) and e["reparto"]["estructura"] == 7.0
    print(f"OK  cotizar           -> 400 m/s cuestan ${costo:.2f} M")

    # 23d. faltante_pct: cuánto le faltó al recurso para su mínimo
    info = jugar(easy, estructura=3.0, propulsion=6.0)
    filas = {f["clave"]: f for f in info["recursos"]}
    assert math.isclose(filas["estructura"]["faltante_pct"], 50) and filas["propulsion"]["faltante_pct"] == 0
    print("OK  faltante_pct      -> 3 kg de 6 kg mínimos = 50 %")

    # 24. Las 5 estrellas deben ser alcanzables en cada nivel
    maximos = {}
    for mid in IDS_NIVELES:
        par = cargar_parametros(mid)
        maximos[mid] = puntaje_maximo(par)
        assert maximos[mid] >= umbrales_estrellas(par)[-1], (mid, maximos[mid])
    print("OK  5 estrellas posibles -> mejor puntaje estimado:", maximos)

    # 25. Validación fina: cada misión se puede completar, con margen razonable y 5 estrellas
    for mid in IDS_NIVELES:
        r = validar_mision_fina(cargar_parametros(mid))
        assert r["completable"] and r["tradeoff"], (mid, r)
        assert r["mejor_estrellas"] == ESTRELLAS_MAX and r["margen_ok"], (mid, r["sugerencia"])
    print("OK  validación fina   -> las 5 misiones completables, 5 estrellas alcanzables")

    # ---- Paso de los botones − y + ----
    esperado = {"easy_cubesat": 0.5, "normal_leo": 1, "hard_mro_marte": 5,
                "harder_perseverance": 5, "insane_artemis1": 4}
    for mid, paso in esperado.items():
        e = iniciar_mision(cargar_parametros(mid))
        p = paso_dinero(e)
        assert abs(p - paso) < 1e-9, (mid, p)
        assert e["presupuesto_musd"] / p >= 25
        # con ese paso se compran todos los mínimos sin pasarse del presupuesto
        assert sum(math.ceil(costo_de(r, r["minimo"]) / p - 1e-9) * p for r in e["recursos"]) \
            <= e["presupuesto_musd"] + 1e-9
    # con un paso fijo de 5, Easy sería imposible: 6->10 kg de estructura + 5 de propulsión = 15 > 14.5
    e = iniciar_mision(cargar_parametros("easy_cubesat"))
    assert sum(math.ceil(costo_de(r, r["minimo"]) / 5 - 1e-9) * 5 for r in e["recursos"]) > 14.5
    print("OK  paso del dinero   ->", esperado)

    # ---- Bloque 2: parrilla y progreso (archivo temporal de prueba) ----
    # La parrilla sale de parametros_misiones.json: misiones.json ya no existe.
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        r_par = Path(tmp) / "parametros.json"
        incompleta = {"mision": "hard_mro", "dificultad": "Hard", "destino": "órbita de Marte", "cohete": "?"}
        r_par.write_text(json.dumps([
            incompleta,                                   # Hard sin parámetros = próximamente
            dict(MISION_PRUEBA, mision="easy_cubesat", dificultad="Easy", nombre="CubeSat"),
            dict(MISION_PRUEBA, mision="normal_leo", dificultad="Normal"),
        ]), encoding="utf-8")

        def estados(prog):
            return {f["id"]: f["estado"] for f in cargar_misiones(prog, r_par)}

        prog = nuevo_progreso()
        parrilla = cargar_misiones(prog, r_par)
        assert [f["id"] for f in parrilla] == ["easy_cubesat", "normal_leo", "hard_mro"]
        assert parrilla[0]["nombre"] == "CubeSat" and parrilla[1]["nombre"] == "Normal Leo"
        assert all("recursos" not in f and "minimo" not in f for f in parrilla)   # nada oculto
        assert estados(prog) == {"easy_cubesat": "disponible", "normal_leo": "bloqueada", "hard_mro": "proximamente"}
        assert puede_jugar(prog, "easy_cubesat", r_par)
        assert not puede_jugar(prog, "normal_leo", r_par)
        print("OK  parrilla nueva   ->", estados(prog))

        # Completar Easy (con la misión de prueba, id cambiado) desbloquea Normal
        e = _mision_lista(2.5, 4.5)
        e["mision"] = "easy_cubesat"
        revisar(e); simular(e)
        registrar_resultado(prog, e)
        assert prog["completadas"]["easy_cubesat"] == puntaje(e)
        assert cargar_misiones(prog, r_par)[0]["estrellas"] == estrellas(e) == prog["estrellas"]["easy_cubesat"] >= 1
        assert estados(prog) == {"easy_cubesat": "completada", "normal_leo": "disponible", "hard_mro": "proximamente"}
        print("OK  desbloqueo       ->", estados(prog))

        # Una misión fallida no cuenta; un mejor puntaje sí reemplaza al anterior
        e2 = _mision_lista(1.0, 1.0); e2["mision"] = "normal_leo"
        revisar(e2); simular(e2); registrar_resultado(prog, e2)
        assert "normal_leo" not in prog["completadas"]
        e3 = _mision_lista(3.0, 4.8); e3["mision"] = "easy_cubesat"; e3["presupuesto_musd"] = 10
        revisar(e3); simular(e3); registrar_resultado(prog, e3)
        assert prog["completadas"]["easy_cubesat"] == 100
        print("OK  mejor puntaje    ->", prog["completadas"])

        # Una misión 'próximamente' en medio no deja a la siguiente bloqueada para siempre
        r_par.write_text(json.dumps([
            dict(MISION_PRUEBA, mision="easy_cubesat", dificultad="Easy"),
            {"mision": "normal_leo", "dificultad": "Normal", "destino": "LEO", "cohete": "?"},
            dict(MISION_PRUEBA, mision="hard_mro", dificultad="Hard"),
        ]), encoding="utf-8")
        assert estados({"completadas": {"easy_cubesat": 80}}) == \
            {"easy_cubesat": "completada", "normal_leo": "proximamente", "hard_mro": "disponible"}
        print("OK  salta próximamente -> Hard se abre al completar Easy")

        # Todas abiertas si Justin lo decide así
        DESBLOQUEO_EN_ORDEN = False
        assert estados(nuevo_progreso())["hard_mro"] == "disponible"
        print("OK  sin orden        -> todas disponibles")
