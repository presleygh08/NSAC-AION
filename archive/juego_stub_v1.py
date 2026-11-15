# juego_stub.py
# Funciones FALSAS con los nombres exactos del contrato Emanuel <-> Gonzalo
# (docs/reparto-v4.md, sección 2.2). Sirven para construir las pantallas
# mientras Emanuel termina juego.py. Cuando juego.py tenga estas funciones,
# las pantallas solo cambian el import:
#     from interfaz import juego_stub as juego   ->   import juego
#
# Solo existe la misión Easy. TODOS los números de PARAMETROS_PROVISIONALES
# son inventados (PROVISIONAL): los valores reales los entrega Chambi en
# datos/parametros_misiones.json.
#
# Regla simple de v4 (sección 7.1): valor del recurso = dinero x tasa.
#
# Probar este archivo con:  python3 interfaz/juego_stub.py

# ---------------------------------------------------------------------------
# Datos de la misión Easy (PROVISIONAL, inventados)
# ---------------------------------------------------------------------------

PARAMETROS_PROVISIONALES = {
    "easy_cubesat": {
        "nombre": "Small CubeSat",          # PROVISIONAL
        "dificultad": "Easy",
        "destino": "LEO",
        "cohete": "Electron",
        "presupuesto_musd": 100,            # M USD (lo pidió Gonzalo)
        # El orden de la lista importa: es el orden del despegue al destino.
        # Si varios recursos fallan, se muestra la falla del primero.
        "recursos": [
            {
                "clave": "estructura",
                "unidad": "points",         # índice 0 a 100 (PROVISIONAL)
                "minimo": 40,               # PROVISIONAL: menos que esto, explota
                "optimo": 70,               # PROVISIONAL
                "tasa_por_musd": 2,         # PROVISIONAL: 1 M USD compra 2 puntos
                "falla": "explota",
                # mensajes.json aún no tiene clave para "explota" (pedir a Justin).
                "clave_mensaje": None,
            },
            {
                "clave": "propulsion",
                "unidad": "m/s",
                "minimo": 200,              # PROVISIONAL: menos que esto, no llega
                "optimo": 350,              # PROVISIONAL
                "tasa_por_musd": 5,         # PROVISIONAL: 1 M USD compra 5 m/s
                "falla": "no_llega",
                "clave_mensaje": "delta_v_insuficiente",
            },
        ],
        # Comprobación de la regla de validez de v4 (sección 6):
        #   costo de los mínimos = 40/2 + 200/5 = 20 + 40 = 60 M USD  <= 100
        #   costo de los óptimos = 70/2 + 350/5 = 35 + 70 = 105 M USD >  100
        # Hay solución, pero no alcanza para dejar todo en el óptimo.

        # PROVISIONAL: el texto final lo escribe Justin (en inglés).
        "pistas": [
            "Low Earth Orbit is close: the trip is short, but the launch shakes the ship hard.",
            "Reaching orbit still needs a good push from the engines.",
        ],
    },
}


# ---------------------------------------------------------------------------
# Funciones de ayuda (no son parte del contrato; empiezan con _)
# ---------------------------------------------------------------------------

def _buscar_recurso(mision, clave):
    """Devuelve el diccionario del recurso con esa clave, o None si no existe."""
    for recurso in mision["recursos"]:
        if recurso["clave"] == clave:
            return recurso
    return None


def _valor_recurso(estado, recurso):
    """Convierte el dinero asignado a un recurso en su valor (dinero x tasa)."""
    dinero = estado["dinero_musd"][recurso["clave"]]
    return dinero * recurso["tasa_por_musd"]


# ---------------------------------------------------------------------------
# Funciones del contrato
# ---------------------------------------------------------------------------

def cargar_misiones():
    """Devuelve la lista de misiones para la parrilla.
    Cada misión es un diccionario: id, nombre, dificultad, destino, cohete, bloqueada."""
    lista = []
    for id_mision in PARAMETROS_PROVISIONALES:
        mision = PARAMETROS_PROVISIONALES[id_mision]
        lista.append({
            "id": id_mision,
            "nombre": mision["nombre"],
            "dificultad": mision["dificultad"],
            "destino": mision["destino"],
            "cohete": mision["cohete"],
            "bloqueada": False,
        })
    return lista


def iniciar_mision(id_mision):
    """Devuelve un estado nuevo para la misión elegida.
    El estado NO tiene mínimos ni óptimos (están ocultos).
    Lanza ValueError si el id no existe."""
    if id_mision not in PARAMETROS_PROVISIONALES:
        raise ValueError("Misión desconocida: " + str(id_mision))
    mision = PARAMETROS_PROVISIONALES[id_mision]

    # Dinero asignado a cada recurso, empieza en 0 M USD.
    dinero = {}
    unidades = {}
    for recurso in mision["recursos"]:
        dinero[recurso["clave"]] = 0
        unidades[recurso["clave"]] = recurso["unidad"]

    return {
        "mision": id_mision,
        "nombre": mision["nombre"],
        "destino": mision["destino"],
        "cohete": mision["cohete"],
        "presupuesto_musd": mision["presupuesto_musd"],   # M USD
        "pistas": list(mision["pistas"]),
        "recursos": list(dinero.keys()),    # claves en orden, p. ej. ["estructura", "propulsion"]
        "unidades": unidades,               # unidad de cada recurso
        "dinero_musd": dinero,              # M USD asignados a cada recurso
    }


def repartir(estado, recurso, dinero):
    """Asigna "dinero" (M USD) al recurso. Reemplaza lo que tenía antes (no suma).
    Devuelve el estado actualizado. Lanza ValueError si el recurso no existe
    o si el dinero es negativo."""
    if recurso not in estado["dinero_musd"]:
        raise ValueError("Recurso desconocido: " + str(recurso))
    if dinero < 0:
        raise ValueError("El dinero no puede ser negativo")
    estado["dinero_musd"][recurso] = dinero
    return estado


def presupuesto_restante(estado):
    """Devuelve cuánto presupuesto queda sin repartir (M USD). Puede ser negativo."""
    gastado = 0
    for clave in estado["dinero_musd"]:
        gastado = gastado + estado["dinero_musd"][clave]
    return estado["presupuesto_musd"] - gastado


def revisar(estado):
    """Revisión CML4: solo comprueba el presupuesto.
    Devuelve {"ok": True/False, "exceso": M USD que sobran del presupuesto (0 si ok)}."""
    restante = presupuesto_restante(estado)
    if restante >= 0:
        return {"ok": True, "exceso": 0}
    return {"ok": False, "exceso": -restante}


def simular(estado):
    """Compara cada recurso con su mínimo oculto.
    Devuelve un diccionario:
      exito:           True si todos los recursos llegan a su mínimo
      fallidos:        lista de claves de recursos bajo su mínimo
      falla_principal: "explota", "no_llega", ... o None si hubo éxito
      clave_mensaje:   clave de datos/mensajes.json (None si aún no existe)
    """
    mision = PARAMETROS_PROVISIONALES[estado["mision"]]
    fallidos = []
    falla_principal = None
    clave_mensaje = "exito"

    for recurso in mision["recursos"]:          # en orden del despegue al destino
        if _valor_recurso(estado, recurso) < recurso["minimo"]:
            fallidos.append(recurso["clave"])
            if falla_principal is None:         # solo el primero que falla
                falla_principal = recurso["falla"]
                clave_mensaje = recurso["clave_mensaje"]

    return {
        "exito": len(fallidos) == 0,
        "fallidos": fallidos,
        "falla_principal": falla_principal,
        "clave_mensaje": clave_mensaje,
    }


def puntaje(estado):
    """Puntaje de 0 a 100. Si la misión falla, es 0.
    Por recurso: 100 x (1 - |valor - óptimo| / óptimo), con 0 como mínimo.
    Devuelve {"total": promedio, "por_recurso": {clave: puntos}}."""
    mision = PARAMETROS_PROVISIONALES[estado["mision"]]
    resultado = simular(estado)

    por_recurso = {}
    suma = 0
    for recurso in mision["recursos"]:
        if resultado["exito"]:
            valor = _valor_recurso(estado, recurso)
            optimo = recurso["optimo"]
            puntos = 100 * (1 - abs(valor - optimo) / optimo)
            if puntos < 0:
                puntos = 0
        else:
            puntos = 0
        por_recurso[recurso["clave"]] = round(puntos)
        suma = suma + puntos

    total = round(suma / len(mision["recursos"]))
    return {"total": total, "por_recurso": por_recurso}


def revelar(estado):
    """Revela, por recurso, lo elegido, el mínimo y el óptimo, con una explicación.
    Devuelve una lista de diccionarios (en el orden de los recursos)."""
    mision = PARAMETROS_PROVISIONALES[estado["mision"]]
    lista = []
    for recurso in mision["recursos"]:
        lista.append({
            "clave": recurso["clave"],
            "unidad": recurso["unidad"],
            "dinero_musd": estado["dinero_musd"][recurso["clave"]],
            "elegido": _valor_recurso(estado, recurso),
            "minimo": recurso["minimo"],
            "optimo": recurso["optimo"],
            # PROVISIONAL: la explicación final la escribe Justin.
            "explicacion": "Provisional values: the real ones will come from NASA data.",
        })
    return lista


# ---------------------------------------------------------------------------
# Pruebas (solo se ejecutan con: python3 interfaz/juego_stub.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    misiones = cargar_misiones()
    assert len(misiones) == 1
    assert misiones[0]["id"] == "easy_cubesat"

    estado = iniciar_mision("easy_cubesat")
    assert presupuesto_restante(estado) == 100
    assert "minimo" not in str(estado)          # nada oculto en el estado

    # Reparto que se pasa del presupuesto: la revisión lo detecta.
    repartir(estado, "estructura", 60)
    repartir(estado, "propulsion", 60)
    assert revisar(estado) == {"ok": False, "exceso": 20}

    # Estructura bajo su mínimo (10 x 2 = 20 < 40): explota primero.
    repartir(estado, "estructura", 10)
    repartir(estado, "propulsion", 30)          # 30 x 5 = 150 < 200
    resultado = simular(estado)
    assert resultado["exito"] is False
    assert resultado["fallidos"] == ["estructura", "propulsion"]
    assert resultado["falla_principal"] == "explota"
    assert puntaje(estado)["total"] == 0

    # Solo propulsión baja: no llega.
    repartir(estado, "estructura", 35)          # 70 = óptimo
    resultado = simular(estado)
    assert resultado["falla_principal"] == "no_llega"
    assert resultado["clave_mensaje"] == "delta_v_insuficiente"

    # Reparto exitoso: estructura en su óptimo, propulsión 65 x 5 = 325 m/s.
    repartir(estado, "propulsion", 65)
    assert revisar(estado)["ok"] is True
    assert simular(estado)["exito"] is True
    resultado_puntaje = puntaje(estado)
    assert resultado_puntaje["por_recurso"]["estructura"] == 100
    assert resultado_puntaje["por_recurso"]["propulsion"] == 93   # 100 x (1 - 25/350)
    assert len(revelar(estado)) == 2

    # Errores esperados.
    try:
        repartir(estado, "potencia", 10)
        assert False, "debió lanzar ValueError"
    except ValueError:
        pass

    print("juego_stub.py: todas las pruebas pasaron")
