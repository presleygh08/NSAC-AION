# nucleo.py
# Núcleo del juego con el flujo de REPARTO DE PRESUPUESTO:
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
import itertools
from pathlib import Path

import fisica
import potencia_costo

CARPETA_DATOS = Path(__file__).parent / "datos"
ARCHIVO_PARAMETROS = "parametros_misiones.json"
ARCHIVO_DESTINOS = "destinos.json"

FALLAS_VALIDAS = ["explota", "no_llega", "se_apaga", "incomunicada"]
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
    {'exito': bool, 'falla': None o 'explota'/'no_llega'/..., 'bajo_minimo': [claves]}.
    Si fallan varios, 'falla' es la del primer recurso en el orden de la lista
    (estructura, propulsión, potencia, comunicaciones)."""
    if estado["fase"] != "simulacion":
        raise ValueError("Primero hay que pasar la revisión (revisar)")
    bajo = [r["clave"] for r in estado["recursos"]
            if valor_recurso(estado, r["clave"]) < r["minimo"] - TOLERANCIA]
    falla = _buscar_recurso(estado, bajo[0])["falla"] if bajo else None
    estado["resultado"] = {"exito": not bajo, "falla": falla, "bajo_minimo": bajo}
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

# BORRADORES de respaldo para las fallas que mensajes.json aún no cubre.
# Justin: añade estas claves a mensajes.json con tu texto; si existen allí,
# se usa el tuyo y este respaldo se ignora.
MENSAJES_RESPALDO = {
    "explota": "The ship broke apart during launch: its structure is {valor} {unidad} and it needs at least {minimo} {unidad} to survive the vibration. The structure is the frame that holds everything together. Try giving more budget to the structure.",
    "incomunicada": "The mission stopped: your link sends only {valor} {unidad} and it needs at least {minimo} {unidad} to reach Earth. A weak antenna cannot send data from far away. Try investing more in communications.",
    "sin_ciencia": "The mission stopped: your instruments reach {valor} {unidad} and the goal needs at least {minimo}. Arriving is not enough if the science does not work. Try investing more in instruments.",
    "fuera_de_tiempo": "The mission stopped: the ship can work only {valor} {unidad} and it needs at least {minimo}. Autonomy limits how long a mission can last. Try investing more in mission time.",
}
MENSAJE_GENERICO = "The mission could not be completed. Try a different budget split."


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


def mensaje_resultado(estado, mensajes=None):
    """Texto explicativo del resultado (usa revelar). Solo después de simular().
    Si la misión falló, explica la PRIMERA falla (la misma que devuelve simular)."""
    if estado["fase"] != "resultado":
        raise ValueError("Primero hay que simular")
    base = {"destino": estado["destino"], "lanzador": estado["cohete"]}
    res = estado["resultado"]
    if res["exito"]:
        return mensaje("exito", mensajes, **base)
    r = _buscar_recurso(estado, res["bajo_minimo"][0])
    valor = valor_recurso(estado, r["clave"])
    datos = dict(base, recurso=r["clave"], unidad=r["unidad"], valor=_num(valor),
                 minimo=_num(r["minimo"]), optimo=_num(r["optimo"]),
                 dv_requerido_m_s=_num(r["minimo"]), dv_disponible_m_s=_num(valor),
                 consumo_w=_num(r["minimo"]), generada_w=_num(valor))
    return mensaje(FALLA_A_MENSAJE.get(r["falla"], r["falla"]), mensajes, **datos)


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


def puntaje(estado):
    """Promedio de los puntos por recurso (0 si la misión falló). Devuelve entero."""
    if estado["fase"] != "resultado":
        raise ValueError("Primero hay que simular")
    if not estado["resultado"]["exito"]:
        return 0
    pts = [puntos_recurso(valor_recurso(estado, r["clave"]), r["optimo"])
           for r in estado["recursos"]]
    return round(sum(pts) / len(pts))


def revelar(estado):
    """Datos para la pantalla de resultados: por recurso, lo elegido, el mínimo,
    el óptimo, sus puntos y si quedó bajo el mínimo / cerca del óptimo.
    Devuelve: {'puntaje', 'exito', 'optimo', 'falla', 'mensaje', 'recursos': [...]}.
      'falla'   -> None si hubo éxito, o 'explota'/'no_llega'/... (la primera falla)
      'mensaje' -> texto explicativo de mensajes.json para mostrar en la pantalla."""
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
            "fuente": r.get("fuente", ""),
        })
    exito = estado["resultado"]["exito"]
    return {"puntaje": puntaje(estado), "exito": exito,
            "optimo": exito and all(f["cerca_optimo"] for f in filas),
            "falla": estado["resultado"]["falla"],
            "mensaje": mensaje_resultado(estado),
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
    """Progreso de un jugador nuevo: {'completadas': {id_mision: mejor_puntaje}}.
    Vive en memoria (así también funciona en la versión web con pygbag)."""
    return {"completadas": {}}


def _nombre_mision(m):
    """Nombre para mostrar: el campo "nombre" si existe; si no, se arma con el id
    ("normal_leo" -> "Normal Leo")."""
    return m.get("nombre") or m["mision"].replace("_", " ").title()


def cargar_misiones(progreso=None, ruta_parametros=None):
    """Lista para la parrilla, ordenada por dificultad. Sale de
    parametros_misiones.json. Cada elemento trae SOLO estos campos (nunca
    mínimos ni óptimos):
      'id', 'nombre', 'dificultad', 'destino', 'cohete', 'presupuesto_musd',
      'estado' y 'mejor_puntaje' (None si no está completada).
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
    misiones = sorted(misiones, key=lambda m: orden.get(m.get("dificultad"), len(orden)))

    parrilla = []
    anterior_completada = True              # la primera misión siempre está abierta
    for m in misiones:
        mid = m["mision"]
        fila = {"id": mid, "nombre": _nombre_mision(m), "dificultad": m.get("dificultad"),
                "destino": m.get("destino"), "cohete": m.get("cohete"),
                "presupuesto_musd": m.get("presupuesto_musd"),
                "mejor_puntaje": progreso["completadas"].get(mid)}
        if mid in progreso["completadas"]:
            fila["estado"] = "completada"
        elif verificar_parametros(m):       # lista de problemas no vacía
            fila["estado"] = "proximamente"
        elif DESBLOQUEO_EN_ORDEN and not anterior_completada:
            fila["estado"] = "bloqueada"
        else:
            fila["estado"] = "disponible"
        if fila["estado"] != "proximamente":
            anterior_completada = mid in progreso["completadas"]
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
    if "--verificar" in sys.argv:        # python nucleo.py --verificar [ruta.json]
        ruta = sys.argv[sys.argv.index("--verificar") + 1:][:1]
        prov = provisionales_archivo(ruta[0] if ruta else None)
        for mid, problemas in verificar_archivo(ruta[0] if ruta else None).items():
            print(f"[{'OK ' if not problemas else 'PENDIENTE'}] {mid}")
            for x in problemas:
                print("   -", x)
            if prov.get(mid):
                print("   * valores PROVISIONALES (esperan a Chambi):", ", ".join(prov[mid]))
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
    assert r["falla"] == "explota" and r["bajo_minimo"] == ["estructura", "propulsion"]
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

    # 16. explota -> usa el respaldo (mensajes.json aún no la trae)
    info = jugar(easy, estructura=3.0, propulsion=6.0)
    assert info["falla"] == "explota" and "{" not in info["mensaje"] and "6 kg" in info["mensaje"]
    print("OK  mensaje explota   ->", info["mensaje"][:45] + "...")

    # 17. Cada falla (también las de Harder e Insane) tiene mensaje completo
    for falla in FALLAS_VALIDAS + ["sin_ciencia", "fuera_de_tiempo"]:
        txt = mensaje(FALLA_A_MENSAJE.get(falla, falla), recurso="x", unidad="u", valor=1,
                      minimo=2, optimo=3, dv_requerido_m_s=2, dv_disponible_m_s=1,
                      consumo_w=2, generada_w=1)
        assert txt != MENSAJE_GENERICO and "{" not in txt, falla
    print("OK  todas las fallas  -> tienen mensaje:", FALLAS_VALIDAS + ["sin_ciencia", "fuera_de_tiempo"])

    # 18. Presupuesto excedido: revisar trae el mensaje con el gasto y el presupuesto
    e = iniciar_mision(easy)
    repartir(e, "estructura", 10.0); repartir(e, "propulsion", 10.0)
    rev = revisar(e)
    assert not rev["ok"] and "20" in rev["mensaje"] and "14.5" in rev["mensaje"] and "{" not in rev["mensaje"]
    e = iniciar_mision(easy)
    repartir(e, "estructura", 8.5); repartir(e, "propulsion", 6.0)
    assert revisar(e)["mensaje"] is None
    print("OK  presupuesto       ->", rev["mensaje"][:45] + "...")

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