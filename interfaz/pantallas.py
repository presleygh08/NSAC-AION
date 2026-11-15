# pantallas.py
# Una función por pantalla. Cada función:
#   1. DIBUJA la pantalla según el estado del juego.
#   2. DEVUELVE la lista de botones que hay en ella.
# Las pantallas NO cambian el estado: solo dibujan. Los clics los procesa
# app.py (función aplicar_accion). Tampoco hay física aquí: los números
# vienen del estado (y luego vendrán de fisica.py / juego.py).
#
# "datos" es un diccionario con todo lo leído de los JSON:
#   datos["textos"], datos["lanzadores"], datos["destinos"], datos["mensajes"]

import pygame

from interfaz import config
from interfaz.componentes import (Boton, BarraRecurso, dibujar_texto,
                                  dibujar_texto_multilinea)

# Medidas que se repiten en varias pantallas.
MARGEN = 40
ANCHO_CONTENIDO = 580        # columna izquierda (opciones)
X_PANEL = 650                # columna derecha (panel de recursos)
Y_BOTONES_NAV = 630          # altura de los botones Back / Next


# ---------------------------------------------------------------------------
# Funciones de ayuda
# ---------------------------------------------------------------------------

def nombre_destino(textos, destino):
    """Traduce el nombre del destino del JSON (en español) al inglés para mostrarlo."""
    return textos["destinos"].get(destino, destino)


def capacidad_para_destino(lanzador, destino):
    """Busca en un lanzador su capacidad (kg) para el destino elegido.
    Devuelve None si no hay dato publicado (null en el JSON) o si no hay destino.
    Es solo lectura de datos, no física."""
    columna = config.COLUMNA_CAPACIDAD.get(destino)
    if columna is None:
        return None
    return lanzador.get(columna)     # puede ser None (null en el JSON)


def buscar_lanzador(datos, nombre):
    """Devuelve el diccionario del lanzador con ese nombre, o None."""
    for lanzador in datos["lanzadores"]:
        if lanzador["nombre"] == nombre:
            return lanzador
    return None


def boton_atras(textos):
    return Boton(textos["botones"]["atras"], MARGEN, Y_BOTONES_NAV, 140, 50, "atras")


def boton_siguiente(textos, activo=True):
    return Boton(textos["botones"]["siguiente"], config.ANCHO - MARGEN - 140,
                 Y_BOTONES_NAV, 140, 50, "siguiente", activo=activo)


def dibujar_titulo(ventana, texto):
    dibujar_texto(ventana, texto, MARGEN, 30, config.LETRA_TITULO)


def dibujar_panel_recursos(ventana, estado, datos):
    """Panel de la derecha con las barras de masa, potencia y presupuesto.
    Está en varias pantallas para que el jugador vea los trade-offs siempre."""
    textos = datos["textos"]
    t = textos["recursos"]

    # Fondo del panel.
    panel = pygame.Rect(X_PANEL - 15, 100, 345, 330)
    pygame.draw.rect(ventana, config.COLOR_PANEL, panel, border_radius=10)

    dibujar_texto(ventana, t["titulo"], X_PANEL, 115)

    # Masa: comparamos la masa seca con la capacidad del lanzador elegido.
    capacidad = None
    lanzador = buscar_lanzador(datos, estado["lanzador"])
    if lanzador is not None:
        capacidad = capacidad_para_destino(lanzador, estado["destino"])
    barra_masa = BarraRecurso(t["masa"], "kg", X_PANEL, 160)
    barra_masa.dibujar(ventana, estado["masa_seca_kg"], capacidad, t["sin_limite"])

    # Potencia: consumo frente a lo que generan los paneles (valores de PRUEBA).
    barra_potencia = BarraRecurso(t["potencia"], "W", X_PANEL, 230)
    barra_potencia.dibujar(ventana, estado["potencia_consumo_w"],
                           estado["potencia_generada_w"])

    # Presupuesto: costo frente al presupuesto (costo de PRUEBA).
    barra_presupuesto = BarraRecurso(t["presupuesto"], "M USD", X_PANEL, 300)
    barra_presupuesto.dibujar(ventana, estado["costo_musd"], estado["presupuesto_musd"])

    # Aviso de que todavía son valores de prueba.
    dibujar_texto_multilinea(ventana, textos["aviso_prueba"], X_PANEL, 370, 310,
                             config.LETRA_PEQUENA, config.COLOR_TEXTO_SUAVE)


# ---------------------------------------------------------------------------
# Pantalla 1: inicio
# ---------------------------------------------------------------------------

def dibujar_inicio(ventana, estado, datos):
    t = datos["textos"]["inicio"]
    centro_x = config.ANCHO // 2

    dibujar_texto(ventana, t["titulo"], centro_x, 220, 60, centrado=True)
    dibujar_texto(ventana, t["subtitulo"], centro_x, 290, centrado=True,
                  color=config.COLOR_TEXTO_SUAVE)
    dibujar_texto_multilinea(ventana, t["instrucciones"], 220, 340, 560)

    boton_empezar = Boton(datos["textos"]["botones"]["empezar"],
                          centro_x - 100, 460, 200, 60, "siguiente")
    return [boton_empezar]


# ---------------------------------------------------------------------------
# Pantalla 2: objetivo (elegir destino)
# ---------------------------------------------------------------------------

def dibujar_objetivo(ventana, estado, datos):
    textos = datos["textos"]
    t = textos["objetivo"]
    dibujar_titulo(ventana, t["titulo"])
    dibujar_texto_multilinea(ventana, t["ayuda"], MARGEN, 85, config.ANCHO - 2 * MARGEN,
                             config.LETRA_PEQUENA, config.COLOR_TEXTO_SUAVE)

    botones = []
    y = 140
    for destino in datos["destinos"]:
        # Armamos la segunda línea con los datos. Si algo es null, lo decimos.
        if destino["delta_v_m_s"] is None:
            texto_dv = textos["sin_datos"]
        else:
            texto_dv = str(destino["delta_v_m_s"]) + " m/s"
        if destino["distancia_ua"] is None:
            texto_dist = textos["sin_datos"]
        else:
            texto_dist = str(destino["distancia_ua"]) + " AU"
        subtexto = (t["delta_v"] + ": " + texto_dv + "   |   "
                    + t["distancia"] + ": " + texto_dist + "   |   "
                    + t["fuente"] + ": " + str(destino["fuente"]))

        boton = Boton(nombre_destino(textos, destino["destino"]),
                      MARGEN, y, config.ANCHO - 2 * MARGEN, 70,
                      "elegir_destino", valor=destino["destino"],
                      seleccionado=(estado["destino"] == destino["destino"]),
                      subtexto=subtexto)
        botones.append(boton)
        y = y + 85

    botones.append(boton_atras(textos))
    # "Next" solo se activa cuando ya hay un destino elegido.
    botones.append(boton_siguiente(textos, activo=(estado["destino"] is not None)))
    return botones


# ---------------------------------------------------------------------------
# Pantalla 3: diseño de la nave
# ---------------------------------------------------------------------------

def dibujar_fila_control(ventana, botones, y, etiqueta, ayuda, clave, valor, unidad, paso):
    """Dibuja una fila con: etiqueta, botón "-", valor actual, botón "+" y ayuda."""
    dibujar_texto(ventana, etiqueta, MARGEN, y)
    botones.append(Boton("-", MARGEN, y + 30, 50, 40, "cambiar", valor=(clave, -paso)))
    dibujar_texto(ventana, str(valor) + " " + unidad, MARGEN + 125, y + 50, centrado=True)
    botones.append(Boton("+", MARGEN + 200, y + 30, 50, 40, "cambiar", valor=(clave, paso)))
    dibujar_texto_multilinea(ventana, ayuda, MARGEN + 270, y + 32, ANCHO_CONTENIDO - 270,
                             config.LETRA_PEQUENA, config.COLOR_TEXTO_SUAVE)


def dibujar_diseno(ventana, estado, datos):
    textos = datos["textos"]
    t = textos["diseno"]
    dibujar_titulo(ventana, t["titulo"])

    botones = []
    limites = config.LIMITES_DISENO
    dibujar_fila_control(ventana, botones, 110, t["masa_seca"], t["masa_seca_ayuda"],
                         "masa_seca_kg", estado["masa_seca_kg"], "kg",
                         limites["masa_seca_kg"][2])
    dibujar_fila_control(ventana, botones, 230, t["area_paneles"], t["area_paneles_ayuda"],
                         "area_paneles_m2", estado["area_paneles_m2"], "m²",
                         limites["area_paneles_m2"][2])
    dibujar_fila_control(ventana, botones, 350, t["isp"], t["isp_ayuda"],
                         "isp_s", estado["isp_s"], "s",
                         limites["isp_s"][2])

    dibujar_panel_recursos(ventana, estado, datos)

    botones.append(boton_atras(textos))
    botones.append(boton_siguiente(textos))
    return botones


# ---------------------------------------------------------------------------
# Pantalla 4: lanzador
# ---------------------------------------------------------------------------

def dibujar_lanzador(ventana, estado, datos):
    textos = datos["textos"]
    t = textos["lanzador"]
    dibujar_titulo(ventana, t["titulo"])

    botones = []
    destino = estado["destino"]
    if destino is None:
        dibujar_texto(ventana, t["sin_destino"], MARGEN, 110)
    else:
        y = 100
        for lanzador in datos["lanzadores"]:
            capacidad = capacidad_para_destino(lanzador, destino)
            # null = no hay dato publicado: lo mostramos, pero no se puede elegir.
            if capacidad is None:
                texto_cap = textos["sin_datos"]
            else:
                texto_cap = str(capacidad) + " kg"
            if lanzador["costo_musd"] is None:
                texto_costo = textos["sin_datos"]
            else:
                texto_costo = str(lanzador["costo_musd"]) + " M USD"
            subtexto = (t["capacidad"] + " " + nombre_destino(textos, destino) + ": "
                        + texto_cap + "   |   " + t["costo"] + ": " + texto_costo)

            boton = Boton(lanzador["nombre"], MARGEN, y, ANCHO_CONTENIDO, 72,
                          "elegir_lanzador", valor=lanzador["nombre"],
                          activo=(capacidad is not None),
                          seleccionado=(estado["lanzador"] == lanzador["nombre"]),
                          subtexto=subtexto)
            botones.append(boton)
            y = y + 82

        # Fuente del lanzador elegido.
        elegido = buscar_lanzador(datos, estado["lanzador"])
        if elegido is not None:
            dibujar_texto(ventana, t["fuente"] + ": " + str(elegido["fuente"]),
                          MARGEN, y + 2, config.LETRA_PEQUENA)

    # Aviso: las cifras no son directamente comparables.
    dibujar_texto_multilinea(ventana, t["aviso"], X_PANEL, 450, 310,
                             config.LETRA_PEQUENA, config.COLOR_TEXTO_SUAVE)

    dibujar_panel_recursos(ventana, estado, datos)

    botones.append(boton_atras(textos))
    # En vez de "Next", aquí el botón es "Launch mission" (acción "simular").
    botones.append(Boton(textos["botones"]["lanzar"], config.ANCHO - MARGEN - 220,
                         Y_BOTONES_NAV, 220, 50, "simular",
                         activo=(estado["lanzador"] is not None)))
    return botones


# ---------------------------------------------------------------------------
# Pantalla 5: resultados
# ---------------------------------------------------------------------------

def dibujar_resultado(ventana, estado, datos):
    textos = datos["textos"]
    t = textos["resultado"]
    dibujar_titulo(ventana, t["titulo"])

    resultado = estado["resultado"]
    if resultado is None:
        dibujar_texto(ventana, t["sin_resultado"], MARGEN, 110)
    else:
        # Buscamos el mensaje por su clave (exito, delta_v_insuficiente, ...)
        # y llenamos los huecos {destino}, {m0_kg}, ... con los valores del resultado.
        plantilla = datos["mensajes"].get(resultado["clave"], resultado["clave"])
        try:
            mensaje = plantilla.format(**resultado["datos_mensaje"])
        except KeyError:
            mensaje = plantilla   # falta algún dato: mostramos la plantilla tal cual

        dibujar_texto(ventana, t["puntaje"] + ": " + str(resultado["puntaje"]),
                      MARGEN, 110, config.LETRA_TITULO, config.COLOR_BARRA_OK)
        dibujar_texto_multilinea(ventana, mensaje, MARGEN, 170, ANCHO_CONTENIDO)

    dibujar_panel_recursos(ventana, estado, datos)

    botones = [boton_atras(textos)]
    botones.append(Boton(textos["botones"]["redisenar"], 380, Y_BOTONES_NAV, 200, 50,
                         "redisenar"))
    botones.append(Boton(textos["botones"]["menu"], config.ANCHO - MARGEN - 200,
                         Y_BOTONES_NAV, 200, 50, "menu"))
    return botones


# ---------------------------------------------------------------------------
# Pantallas PROVISIONALES del flujo v4 (solo título, aviso y botones).
# Todavía no usan interfaz/juego_stub.py: eso es el siguiente paso.
# ---------------------------------------------------------------------------

def dibujar_provisional(ventana, textos, clave):
    """Dibuja el título y el aviso "Coming soon" de la pantalla con esa clave
    (la clave es la sección de textos_en.json: "parrilla", "taller", ...)."""
    t = textos[clave]
    dibujar_titulo(ventana, t["titulo"])
    dibujar_texto_multilinea(ventana, t["pendiente"], MARGEN, 110, config.ANCHO - 2 * MARGEN,
                             config.LETRA_NORMAL, config.COLOR_TEXTO_SUAVE)


def dibujar_parrilla(ventana, estado, datos):
    textos = datos["textos"]
    dibujar_provisional(ventana, textos, "parrilla")
    # Es la primera pantalla: no hay "Back", solo "Next".
    return [boton_siguiente(textos)]


def dibujar_taller(ventana, estado, datos):
    textos = datos["textos"]
    dibujar_provisional(ventana, textos, "taller")
    return [boton_atras(textos), boton_siguiente(textos)]


def dibujar_revision(ventana, estado, datos):
    textos = datos["textos"]
    dibujar_provisional(ventana, textos, "revision")
    # En vez de "Next", el botón es "Launch mission" (acción "simular"),
    # que guarda el resultado y lleva a la pantalla de resultado.
    boton_lanzar = Boton(textos["botones"]["lanzar"], config.ANCHO - MARGEN - 220,
                         Y_BOTONES_NAV, 220, 50, "simular")
    return [boton_atras(textos), boton_lanzar]


# ---------------------------------------------------------------------------
# Elegir qué pantalla dibujar
# ---------------------------------------------------------------------------
# NOTA: dibujar_inicio, dibujar_diseno y dibujar_lanzador son del flujo viejo.
# Ya no se usan; las dejamos por si reutilizamos partes en las pantallas nuevas.

def dibujar_pantalla(ventana, estado, datos):
    """Llama a la función de la pantalla actual y devuelve sus botones."""
    pantalla = estado["pantalla"]
    if pantalla == "parrilla":
        return dibujar_parrilla(ventana, estado, datos)
    elif pantalla == "objetivo":
        return dibujar_objetivo(ventana, estado, datos)
    elif pantalla == "taller":
        return dibujar_taller(ventana, estado, datos)
    elif pantalla == "revision":
        return dibujar_revision(ventana, estado, datos)
    elif pantalla == "resultado":
        return dibujar_resultado(ventana, estado, datos)
    return []
