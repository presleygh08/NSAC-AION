
import random
import json
from pathlib import Path
from fisica import masa_propelente, delta_v
from potencia_costo import potencia_generada, balance_potencia, costo_total

CARPETA_DATOS = Path(__file__).parent / "datos"

COLUMNAS_ESPERADAS = {
    "lanzadores": ["nombre", "capacidad_leo_kg", "capacidad_luna_kg",
                   "capacidad_marte_kg", "costo_musd", "fuente"],
    "destinos": ["destino", "delta_v_m_s", "distancia_ua", "fuente"],
}

# Textos PROVISIONALES, uno por resultado del contrato. Los de Justin los reemplazan.
MENSAJES_POR_DEFECTO = {
    "exito": "Misión cumplida.",
    "delta_v_insuficiente": "La nave no tiene propelente suficiente para el destino.",
    "potencia_insuficiente": "Los paneles no generan la potencia que la nave consume.",
    "masa_excede_lanzador": "La nave pesa más de lo que el lanzador puede llevar.",
    "presupuesto_excedido": "El costo total supera el presupuesto.",
    "falla_aleatoria": "Un imprevisto durante el tránsito dañó la nave.",
}

# Puntos por resultado. Propuesta mía; Justin puede ajustar los valores.
PUNTOS_POR_RESULTADO = {
    "exito": 1000,
    "falla_aleatoria": 200,   # el diseño era correcto, falló el azar
}

# A qué columna de lanzadores.json corresponde cada destino
CAPACIDAD_POR_DESTINO = {
    "LEO": "capacidad_leo_kg",
    "órbita lunar": "capacidad_luna_kg",
    "órbita de Marte": "capacidad_marte_kg",
    "superficie de Marte": "capacidad_marte_kg",
}




#Datos: leer y verificar
def cargar_json(nombre_archivo):
    """Lee un archivo de la carpeta datos/. Devuelve lista o diccionario."""
    with open(CARPETA_DATOS / nombre_archivo, encoding="utf-8") as f:
        return json.load(f)


def leer_mensajes_json():
    """Lee datos/mensajes.json si existe.
    Devuelve (mensajes, problema): mensajes es un dict (vacío si no hay archivo
    o no es válido); problema es un texto, o None si todo está bien."""
    ruta = CARPETA_DATOS / "mensajes.json"
    if not ruta.exists():
        return {}, None
    try:
        with open(ruta, encoding="utf-8") as f:
            contenido = json.load(f)
    except json.JSONDecodeError as e:
        return {}, (f"mensajes.json no es un JSON válido ({e.msg}, línea {e.lineno}); "
                    "se usan los textos provisionales")
    if not isinstance(contenido, dict):
        return {}, ("mensajes.json debe ser un diccionario {clave: texto}; "
                    "se usan los textos provisionales")
    return contenido, None


def cargar_mensajes():
    """Textos de resultado: los provisionales, reemplazados por los de mensajes.json.
    Devuelve: diccionario {clave: texto}."""
    mensajes = dict(MENSAJES_POR_DEFECTO)
    mensajes.update(leer_mensajes_json()[0])
    return mensajes


def cargar_datos():
    """Carga todos los datos del juego. Devuelve un diccionario con 3 entradas."""
    return {
        "lanzadores": cargar_json("lanzadores.json"),
        "destinos": cargar_json("destinos.json"),
        "mensajes": cargar_mensajes(),
    }


def verificar_datos(datos):
    """Revisa columnas de lanzadores y destinos, y el estado de mensajes.json.
    Devuelve: lista de problemas (vacía si todo está bien)."""
    problemas = []
    for tabla, columnas in COLUMNAS_ESPERADAS.items():
        for fila in datos[tabla]:
            for c in columnas:
                if c not in fila:
                    problemas.append(f"{tabla}: falta '{c}' en {fila}")
    problema_mensajes = leer_mensajes_json()[1]
    if problema_mensajes:
        problemas.append(problema_mensajes)
    return problemas


def delta_v_destino(datos, destino):
    """Delta-v total (m/s) del destino, medido desde la superficie terrestre."""
    for fila in datos["destinos"]:
        if fila["destino"] == destino:
            return fila["delta_v_m_s"]
    disponibles = [f["destino"] for f in datos["destinos"]]
    raise ValueError(f"Destino desconocido: '{destino}'. Disponibles: {disponibles}")


def delta_v_nave(datos, destino):
    """Delta-v (m/s) que debe aportar la propia nave.
    destinos.json mide desde la superficie; el lanzador cubre hasta LEO,
    así que a la nave le corresponde la diferencia."""
    return delta_v_destino(datos, destino) - delta_v_destino(datos, "LEO")


def texto_resultado(datos, resultado):
    """Mensaje que explica el resultado (clave de mensajes.json)."""
    return datos["mensajes"][resultado]


def distancia_ua_destino(datos, destino):
    """Distancia al Sol (UA) del destino, según destinos.json."""
    for fila in datos["destinos"]:
        if fila["destino"] == destino:
            return fila["distancia_ua"]
    raise ValueError(f"Destino desconocido: '{destino}'")




#Estado de la misión
def nueva_mision():
    """Crea el estado de una misión nueva. Devuelve: diccionario 'mision'."""
    return {
        "fase": "objetivo",         # objetivo, diseno, lanzador, transito, resultado
        "destino": None,
        "presupuesto_musd": 150,    # M USD disponibles
        # --- decisiones del jugador ---
        "isp": 320,                 # s
        "m_seca_kg": 0,             # kg, nave sin propelente
        "m_prop_cargada_kg": None,  # kg; None = carga el mínimo necesario
        "area_panel_m2": 0,         # m^2
        "eficiencia_panel": 0.30,   # entre 0 y 1
        "consumos_w": [],           # lista de consumos en W
        "costo_nave_musd": 0,
        "costo_instrumentos_musd": 0,
        "lanzador": None,
        # --- calculado por el juego ---
        "delta_v_m_s": 0,           # lo que exige el destino a la nave
        "m_prop_kg": 0,             # propelente mínimo necesario
        "potencia_w": 0,
        "consumo_w": 0,
        "reglas": [],
        "resultado": None,
        "mensaje": "",
        "puntaje": 0,
    }
    """Crea el estado de una misión nueva, con valores iniciales.
    Devuelve: diccionario 'mision'."""
    return {
        "fase": "objetivo",       # objetivo, diseno, lanzador, transito, resultado
        "destino": None,          # nombre del destino elegido (ej. "Luna")
        "presupuesto_musd": 150,  # M USD disponibles
        "isp": 320,               # s (motor)
        "m_seca_kg": 0,           # kg (nave sin propelente)
        "m_prop_kg": 0,           # kg (se calcula con masa_propelente)
        "potencia_w": 0,          # W generados
        "consumo_w": 0,           # W consumidos
        "lanzador": None,         # nombre del lanzador elegido
        "resultado": None,        # "exito" o una clave de falla
        "puntaje": 0,
    }




    """Fija la nave y calcula el propelente que exige el destino.
    m_seca_kg: kg | isp: s | datos: salida de cargar_datos()."""
    dv = delta_v_destino(datos, mision["destino"])
    mision["m_seca_kg"] = m_seca_kg
    mision["isp"] = isp
    mision["m_prop_kg"] = masa_propelente(dv, isp, m_seca_kg)
    mision["fase"] = "lanzador"
    return mision


def propelente_cargado_kg(mision):
    """Propelente que lleva la nave (kg): el que eligió el jugador o, si no
    eligió, el mínimo necesario."""
    carga = mision["m_prop_cargada_kg"]
    return mision["m_prop_kg"] if carga is None else carga


def masa_total_kg(mision):
    """Masa al lanzamiento: nave seca + propelente cargado (kg)."""
    return mision["m_seca_kg"] + propelente_cargado_kg(mision)




#Fases, en el orden en que ocurren
def elegir_destino(mision, destino):
    """Fija el destino y pasa a la fase de diseño.
    destino: str | Devuelve: la misma mision modificada."""
    mision["destino"] = destino
    mision["fase"] = "diseno"
    return mision


def disenar_nave(mision, m_seca_kg, isp, datos):
    """Fija la nave y calcula el propelente que exige el destino.
    m_seca_kg: kg | isp: s | datos: salida de cargar_datos()."""
    dv = delta_v_nave(datos, mision["destino"])
    mision["delta_v_m_s"] = dv
    mision["m_seca_kg"] = m_seca_kg
    mision["isp"] = isp
    mision["m_prop_kg"] = masa_propelente(dv, isp, m_seca_kg)
    mision["fase"] = "lanzador"
    return mision


def elegir_lanzador(mision, lanzador):
    """Guarda el nombre del lanzador y pasa al tránsito. lanzador: str."""
    mision["lanzador"] = lanzador
    mision["fase"] = "transito"
    return mision




#Reglas
def buscar_lanzador(datos, nombre):
    """Fila de lanzadores.json con ese nombre (dict)."""
    for fila in datos["lanzadores"]:
        if fila["nombre"] == nombre:
            return fila
    disponibles = [f["nombre"] for f in datos["lanzadores"]]
    raise ValueError(f"Lanzador desconocido: '{nombre}'. Disponibles: {disponibles}")


def capacidad_lanzador(datos, lanzador, destino):
    """Capacidad (kg) del lanzador para ese destino.
    Devuelve: número, o None si el lanzador no tiene capacidad registrada ahí."""
    if destino not in CAPACIDAD_POR_DESTINO:
        raise ValueError(f"Destino sin columna de capacidad: '{destino}'")
    return buscar_lanzador(datos, lanzador)[CAPACIDAD_POR_DESTINO[destino]]


def compatibilidad_lanzador(mision, datos):
    """Compara la masa total de la nave con la capacidad del lanzador elegido.
    Devuelve: dict con 'ok' (bool), 'masa_kg', 'capacidad_kg' (None si no hay)
    y 'margen_kg' (capacidad - masa; None si no hay capacidad)."""
    masa = masa_total_kg(mision)
    capacidad = capacidad_lanzador(datos, mision["lanzador"], mision["destino"])
    if capacidad is None:
        return {"ok": False, "masa_kg": masa, "capacidad_kg": None, "margen_kg": None}
    return {"ok": masa <= capacidad, "masa_kg": masa,
            "capacidad_kg": capacidad, "margen_kg": capacidad - masa}


def evaluar_reglas(mision, datos):
    """Evalúa las 4 reglas de diseño, en orden de prioridad del resultado.
    También guarda potencia_w y consumo_w en la misión.
    Devuelve: lista de dicts {'clave', 'ok', 'valor', 'limite', 'unidad'}."""
    # 1. Delta-v: lo que logra el propelente cargado frente a lo que exige el destino
    carga = propelente_cargado_kg(mision)
    dv_logrado = delta_v(mision["isp"], mision["m_seca_kg"] + carga, mision["m_seca_kg"])
    dv_requerido = mision["delta_v_m_s"]

    # 2. Potencia: generación del panel frente al consumo
    distancia = distancia_ua_destino(datos, mision["destino"])
    generada = potencia_generada(distancia, mision["area_panel_m2"],
                                 mision["eficiencia_panel"])
    consumo = sum(mision["consumos_w"])
    mision["potencia_w"] = generada
    mision["consumo_w"] = consumo

    # 3. Masa total frente a la capacidad del lanzador
    comp = compatibilidad_lanzador(mision, datos)

    # 4. Costo total frente al presupuesto
    costo_lanzador = buscar_lanzador(datos, mision["lanzador"])["costo_musd"]
    costo = costo_total(costo_lanzador, mision["costo_nave_musd"],
                        mision["costo_instrumentos_musd"])

    return [
        {"clave": "delta_v_insuficiente",
         "ok": dv_logrado >= dv_requerido - 1e-6,   # tolerancia por redondeo
         "valor": dv_logrado, "limite": dv_requerido, "unidad": "m/s"},
        {"clave": "potencia_insuficiente",
         "ok": balance_potencia(generada, mision["consumos_w"]) >= 0,
         "valor": generada, "limite": consumo, "unidad": "W"},
        {"clave": "masa_excede_lanzador",
         "ok": comp["ok"],
         "valor": comp["masa_kg"], "limite": comp["capacidad_kg"], "unidad": "kg"},
        {"clave": "presupuesto_excedido",
         "ok": costo <= mision["presupuesto_musd"],
         "valor": costo, "limite": mision["presupuesto_musd"], "unidad": "M USD"},
    ]


def evaluar_mision(mision, datos=None, p_falla=0.15, rng=random):
    """Evalúa la misión: reglas de diseño, azar, resultado y puntaje.
    datos: salida de cargar_datos() (si es None, se cargan aquí).
    Deja en 'mision': resultado, mensaje, puntaje, reglas, potencia_w, consumo_w.
    Devuelve: la misma misión modificada."""
    if datos is None:
        datos = cargar_datos()

    reglas = evaluar_reglas(mision, datos)
    fallas = [r["clave"] for r in reglas if not r["ok"]]

    if fallas:
        resultado = fallas[0]               # la primera falla en orden de prioridad
    elif evento_aleatorio(p_falla, rng):    # el azar solo cuenta si el diseño es válido
        resultado = "falla_aleatoria"
    else:
        resultado = "exito"

    mision["reglas"] = reglas
    mision["resultado"] = resultado
    mision["mensaje"] = texto_resultado(datos, resultado)
    mision["puntaje"] = calcular_puntaje(mision)
    mision["fase"] = "resultado"
    return mision




#Azar y puntaje
def evento_aleatorio(p, rng=random):
    """Decide si ocurre una falla aleatoria.
    p: probabilidad entre 0 y 1 | rng: generador (el módulo random o random.Random(semilla))
    Devuelve: True si ocurre la falla."""
    if not 0 <= p <= 1:
        raise ValueError("p debe estar entre 0 y 1")
    return rng.random() < p


def calcular_puntaje(mision):
    """Puntaje según el resultado de la misión (0 si el resultado no puntúa).
    Devuelve: puntaje entero."""
    return PUNTOS_POR_RESULTADO.get(mision["resultado"], 0)




#Prueba de los 5 resultados
def _mision_de_prueba(datos, lanzador="Falcon Heavy"):
    """Misión válida hacia la órbita lunar (solo para pruebas)."""
    m = nueva_mision()
    elegir_destino(m, "órbita lunar")
    disenar_nave(m, 500, 320, datos)
    elegir_lanzador(m, lanzador)
    m["area_panel_m2"] = 10
    m["consumos_w"] = [300, 450, 200]
    m["costo_nave_musd"] = 20
    m["costo_instrumentos_musd"] = 15
    return m




#Pruebas
if __name__ == "__main__":
    datos = cargar_datos()
    print("Problemas:", verificar_datos(datos))

    # 1. Misión válida, sin azar -> éxito
    m = evaluar_mision(_mision_de_prueba(datos), datos, p_falla=0)
    assert m["resultado"] == "exito" and m["puntaje"] == 1000, m["resultado"]
    print("OK  válida          ->", m["resultado"], m["puntaje"])

    # 2. Lanzador demasiado pequeño (Electron, 30 kg a la Luna)
    m = evaluar_mision(_mision_de_prueba(datos, "Electron"), datos, p_falla=0)
    assert m["resultado"] == "masa_excede_lanzador", m["resultado"]
    print("OK  Electron        ->", m["resultado"], m["puntaje"])

    # 3. Propelente insuficiente (800 kg en lugar de ~1289 kg)
    m = _mision_de_prueba(datos)
    m["m_prop_cargada_kg"] = 800
    evaluar_mision(m, datos, p_falla=0)
    assert m["resultado"] == "delta_v_insuficiente", m["resultado"]
    print("OK  poco propelente ->", m["resultado"], f"({m['reglas'][0]['valor']:.0f} m/s)")

    # 4. Panel demasiado pequeño (0,5 m^2)
    m = _mision_de_prueba(datos)
    m["area_panel_m2"] = 0.5
    evaluar_mision(m, datos, p_falla=0)
    assert m["resultado"] == "potencia_insuficiente", m["resultado"]
    print("OK  panel pequeño   ->", m["resultado"])

    # 5. Lanzador carísimo (SLS) -> presupuesto excedido
    m = evaluar_mision(_mision_de_prueba(datos, "SLS block 1"), datos, p_falla=0)
    assert m["resultado"] == "presupuesto_excedido", m["resultado"]
    print("OK  SLS             ->", m["resultado"])

    # 6. Diseño válido, pero el azar falla (p = 1)
    m = evaluar_mision(_mision_de_prueba(datos), datos, p_falla=1)
    assert m["resultado"] == "falla_aleatoria" and m["puntaje"] == 200
    print("OK  azar            ->", m["resultado"], m["puntaje"])
    print(m["mensaje"])

