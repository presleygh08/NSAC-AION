# nucleo.py
# Núcleo del juego con el flujo de REPARTO DE PRESUPUESTO.
#
# Flujo:  iniciar_mision -> repartir (varias veces) -> revisar -> simular
#         -> puntaje / revelar
#
# Reglas:
#  - Cada recurso tiene un MÍNIMO y un ÓPTIMO ocultos (vienen de
#    datos/parametros_misiones.json, que llena Chambi).
#  - El jugador reparte dinero (M USD). valor = dinero * tasa del recurso.
#  - Si algún valor queda bajo su mínimo, la misión falla.
#  - Si no falla, el puntaje depende de qué tan cerca está cada valor del óptimo.
#
# La interfaz (Gonzalo) SOLO llama a estas funciones. No lee mínimos ni óptimos
# directamente: usa recursos_visibles() mientras reparte y revelar() al final.

import json
import itertools
from pathlib import Path

CARPETA_DATOS = Path(__file__).parent / "datos"
ARCHIVO_PARAMETROS = "parametros_misiones.json"

FALLAS_VALIDAS = ["explota", "no_llega", "se_apaga", "incomunicada"]
MARGEN_OPTIMO = 0.10   # un recurso es "óptimo" si está a ±10 % de su óptimo (Justin puede cambiarlo)
TOLERANCIA = 1e-9      # evita errores de redondeo al comparar números decimales


# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------

def cargar_parametros(mision_id, ruta=None):
    """Lee parametros_misiones.json y devuelve el diccionario de esa misión.
    El archivo es una lista de misiones; cada una tiene la clave "mision"."""
    ruta = Path(ruta) if ruta else CARPETA_DATOS / ARCHIVO_PARAMETROS
    with open(ruta, encoding="utf-8") as f:
        misiones = json.load(f)
    for m in misiones:
        if m["mision"] == mision_id:
            return m
    disponibles = [m["mision"] for m in misiones]
    raise ValueError(f"Misión desconocida: '{mision_id}'. Disponibles: {disponibles}")


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------

def iniciar_mision(parametros):
    """Crea el estado de una misión nueva a partir de sus parámetros.
    Devuelve: diccionario 'estado'."""
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
    Por ahora es lineal: valor = dinero / (M USD que cuesta cada unidad).
    PASO 2: para propulsión y potencia, reemplazar por fisica.delta_v(...) y
    potencia_costo.potencia_generada(...) (ver sección 7.1 del bosquejo)."""
    return dinero_musd / recurso["musd_por_unidad"]


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


def recursos_visibles(estado):
    """Lo que la interfaz puede mostrar MIENTRAS el jugador reparte
    (sin mínimos ni óptimos). Devuelve lista de dicts."""
    return [{"clave": r["clave"], "unidad": r["unidad"],
             "dinero_musd": estado["reparto"][r["clave"]],
             "valor": valor_recurso(estado, r["clave"])}
            for r in estado["recursos"]]


def revisar(estado):
    """CML 4: solo verifica que el reparto no supere el presupuesto.
    Devuelve: {'ok': bool, 'exceso_musd': float}. Si ok, pasa a 'simulacion'."""
    exceso = gasto_total(estado) - estado["presupuesto_musd"]
    ok = exceso <= TOLERANCIA
    if ok:
        estado["fase"] = "simulacion"
    return {"ok": ok, "exceso_musd": max(exceso, 0.0)}


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
    Devuelve: {'puntaje', 'exito', 'optimo', 'recursos': [...]}."""
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
            "recursos": filas}


# ---------------------------------------------------------------------------
# Verificación de parametros_misiones.json (para Chambi y para el juego)
# ---------------------------------------------------------------------------

def _es_numero_positivo(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x > 0


def verificar_parametros(m):
    """Revisa los parámetros de UNA misión. Devuelve la lista de problemas
    (vacía si está completa y es coherente). Una misión solo es jugable si
    la lista está vacía."""
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
        for campo in ("minimo", "optimo", "musd_por_unidad"):
            if not _es_numero_positivo(r.get(campo)):
                p.append(f"{mid}/{c}: falta '{campo}' (número mayor que 0)")
                completos = False
        for campo in ("unidad", "falla", "fuente"):
            if not r.get(campo):
                p.append(f"{mid}/{c}: falta '{campo}'")
        if r.get("falla") and r["falla"] not in FALLAS_VALIDAS:
            p.append(f"{mid}/{c}: 'falla' debe ser una de {FALLAS_VALIDAS}")
        if completos and r["minimo"] > r["optimo"]:
            p.append(f"{mid}/{c}: el mínimo ({r['minimo']}) supera al óptimo ({r['optimo']})")
        if completos:
            costo_min += r["minimo"] * r["musd_por_unidad"]
            costo_opt += r["optimo"] * r["musd_por_unidad"]
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
# misiones.json (lo escribe Piero) es una lista; cada misión tiene al menos:
#   {"id": "easy_cubesat", "nombre": "...", "dificultad": "Easy",
#    "destino": "LEO", "cohete": "Electron"}
# (también se acepta la clave "mision" en lugar de "id").
# Una misión es JUGABLE si tiene datos en parametros_misiones.json; si no,
# se muestra como "próximamente".

DIFICULTADES = ["Easy", "Normal", "Hard", "Harder", "Insane"]   # orden de la parrilla
DESBLOQUEO_EN_ORDEN = True    # Justin decide; False = todas abiertas desde el inicio


def nuevo_progreso():
    """Progreso de un jugador nuevo: {'completadas': {id_mision: mejor_puntaje}}.
    Vive en memoria (así también funciona en la versión web con pygbag)."""
    return {"completadas": {}}


def _id_mision(m):
    return m["id"] if "id" in m else m["mision"]


def _ids_con_parametros(ruta=None):
    """Ids de las misiones cuyos parámetros están COMPLETOS y válidos
    (las que Chambi aún no termina salen como 'próximamente')."""
    ruta = Path(ruta) if ruta else CARPETA_DATOS / ARCHIVO_PARAMETROS
    if not ruta.exists():
        return set()
    with open(ruta, encoding="utf-8") as f:
        return {_id_mision(m) for m in json.load(f) if verificar_parametros(m) == []}


def cargar_misiones(progreso=None, ruta_misiones=None, ruta_parametros=None):
    """Lista para la parrilla, ordenada por dificultad. Cada elemento trae los
    datos de misiones.json más:
      'id', 'estado' y 'mejor_puntaje' (None si no está completada).
    'estado' es una de:
      'completada'    -> ya se completó (se puede repetir)
      'disponible'    -> se puede jugar
      'bloqueada'     -> hay que completar la anterior (si DESBLOQUEO_EN_ORDEN)
      'proximamente'  -> aún no tiene parámetros (Hard, Harder, Insane...)"""
    progreso = progreso if progreso is not None else nuevo_progreso()
    ruta = Path(ruta_misiones) if ruta_misiones else CARPETA_DATOS / "misiones.json"
    with open(ruta, encoding="utf-8") as f:
        misiones = json.load(f)
    jugables = _ids_con_parametros(ruta_parametros)
    orden = {d: i for i, d in enumerate(DIFICULTADES)}
    misiones = sorted(misiones, key=lambda m: orden.get(m["dificultad"], len(orden)))

    parrilla = []
    anterior_completada = True              # la primera misión siempre está abierta
    for m in misiones:
        mid = _id_mision(m)
        fila = dict(m)
        fila["id"] = mid
        fila["mejor_puntaje"] = progreso["completadas"].get(mid)
        if mid in progreso["completadas"]:
            fila["estado"] = "completada"
        elif mid not in jugables:
            fila["estado"] = "proximamente"
        elif DESBLOQUEO_EN_ORDEN and not anterior_completada:
            fila["estado"] = "bloqueada"
        else:
            fila["estado"] = "disponible"
        anterior_completada = mid in progreso["completadas"]
        parrilla.append(fila)
    return parrilla


def puede_jugar(progreso, mision_id, ruta_misiones=None, ruta_parametros=None):
    """True si la misión está 'disponible' o 'completada' (repetirla)."""
    for fila in cargar_misiones(progreso, ruta_misiones, ruta_parametros):
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
        for mid, problemas in verificar_archivo(ruta[0] if ruta else None).items():
            print(f"[{'OK ' if not problemas else 'PENDIENTE'}] {mid}")
            for x in problemas:
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

    # ---- Bloque 2: parrilla y progreso (archivos temporales de prueba) ----
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        r_mis = Path(tmp) / "misiones.json"
        r_par = Path(tmp) / "parametros.json"
        r_mis.write_text(json.dumps([
            {"id": "hard_mro", "nombre": "MRO", "dificultad": "Hard", "destino": "órbita de Marte", "cohete": "?"},
            {"id": "easy_cubesat", "nombre": "CubeSat", "dificultad": "Easy", "destino": "LEO", "cohete": "Electron"},
            {"id": "normal_leo", "nombre": "LEO", "dificultad": "Normal", "destino": "LEO", "cohete": "Falcon 9"},
        ]), encoding="utf-8")
        # Solo Easy y Normal tienen parámetros (Hard = próximamente)
        r_par.write_text(json.dumps([dict(MISION_PRUEBA, mision="easy_cubesat"), dict(MISION_PRUEBA, mision="normal_leo")]), encoding="utf-8")

        def estados(prog):
            return {f["id"]: f["estado"] for f in cargar_misiones(prog, r_mis, r_par)}

        prog = nuevo_progreso()
        assert [f["id"] for f in cargar_misiones(prog, r_mis, r_par)] == ["easy_cubesat", "normal_leo", "hard_mro"]
        assert estados(prog) == {"easy_cubesat": "disponible", "normal_leo": "bloqueada", "hard_mro": "proximamente"}
        assert puede_jugar(prog, "easy_cubesat", r_mis, r_par)
        assert not puede_jugar(prog, "normal_leo", r_mis, r_par)
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

        # Todas abiertas si Justin lo decide así
        DESBLOQUEO_EN_ORDEN = False
        assert estados(nuevo_progreso())["normal_leo"] == "disponible"
        print("OK  sin orden        -> Normal disponible")
