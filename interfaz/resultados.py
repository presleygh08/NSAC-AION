# resultados.py
# Pantalla de resultados (sección 6 de la especificación).
# Todo sale de nucleo.revelar(estado), que app.py guarda en ui["revelado"]
# (y llama a registrar_resultado una sola vez al entrar; ui["resultados_t0"] es el
# segundo en que se entró, para las animaciones).
#
#   Victoria: "Mission complete!", 5 estrellas que aparecen una por una, el puntaje que
#             cuenta hacia arriba, sello "Optimal design!" y una tabla con, por recurso,
#             tu valor, el mínimo, el óptimo, los puntos y una barra con marcas de mínimo
#             (rojo) y óptimo (verde). Fila "Budget used". El mensaje de revelar debajo.
#   Derrota:  título rojo con la falla principal; los recursos bajo el mínimo con
#             "X of Y needed", % faltante y "Just short / Short / Far below"; la tabla
#             que revela mínimo y óptimo de TODOS los recursos; y el porqué de cada falla.

import pygame

from interfaz import config, estilo, sprites
from interfaz.componentes import (Boton, formatear_musd, formatear_numero, nombre_recurso,
                                  traducir)

X_IZQ = 20
ANCHO_UTIL = config.ANCHO - 2 * X_IZQ
# Columnas de la tabla: recurso, tu valor, mínimo, óptimo, puntos, barra
X_COLUMNAS = [28, 186, 264, 336, 412, 462]
ANCHO_BARRA = 148
Y_LIMITE = 318            # nada de texto por debajo (ahí van los botones)


# ---------------------------------------------------------------------------
# Ayudas
# ---------------------------------------------------------------------------

def segundos_en_pantalla(ui):
    return ui["tiempo"] - ui.get("resultados_t0", ui["tiempo"])


def etiqueta_faltante(textos, pct):
    """'Just short' (< 10 %), 'Short' (10-30 %) o 'Far below' (> 30 %)."""
    etiquetas = textos["resultados"]["etiquetas_faltante"]
    if pct < config.FALTANTE_POCO:
        return etiquetas["poco"]
    if pct <= config.FALTANTE_MEDIO:
        return etiquetas["medio"]
    return etiquetas["mucho"]


def con_unidad(textos, numero, unidad):
    return formatear_numero(numero) + " " + traducir(textos["unidades"], unidad)


def dibujar_barra(sup, x, y, ancho, fila):
    """Barra del recurso: tu valor relleno (verde si llega al mínimo, rojo si no),
    marca roja en el mínimo y marca verde en el óptimo."""
    tope = max(fila["optimo"] * 1.4, fila["valor"], fila["minimo"]) * 1.05
    pygame.draw.rect(sup, config.NEGRO, (x, y, ancho, 8))
    color = config.COLOR_ERROR if fila["bajo_minimo"] else config.COLOR_OK
    largo = int(ancho * min(1.0, fila["valor"] / tope))
    pygame.draw.rect(sup, color, (x, y + 1, largo, 6))
    for valor, color_marca in ((fila["minimo"], config.ROJO), (fila["optimo"], config.VERDE)):
        xm = x + int(ancho * valor / tope)
        pygame.draw.rect(sup, config.BLANCO, (xm - 1, y - 3, 3, 14))     # borde para que se vea
        pygame.draw.rect(sup, color_marca, (xm, y - 2, 1, 12))


def texto_limitado(sup, contenido, x, y, ancho, tamano=config.LETRA_PEQUENA, color=config.COLOR_TEXTO):
    """Como texto_multilinea, pero no escribe por debajo de Y_LIMITE (termina con '...')."""
    alto = estilo.fuente(tamano).get_linesize()
    lineas = estilo.partir_lineas(contenido, ancho, tamano)
    for i in range(len(lineas)):
        if y + alto > Y_LIMITE:
            return y
        linea = lineas[i]
        if y + 2 * alto > Y_LIMITE and i < len(lineas) - 1:
            linea = linea + " ..."
        estilo.texto(sup, linea, x, y, tamano, color)
        y = y + alto
    return y


# ---------------------------------------------------------------------------
# Tabla con el revelado de todos los recursos
# ---------------------------------------------------------------------------

def dibujar_tabla(sup, textos, revelado, y, alto_fila):
    """Panel con una fila por recurso (en rojo las que quedaron bajo el mínimo) y la fila
    "Budget used". Devuelve la y donde terminó."""
    t = textos["resultados"]
    col = t["columnas"]
    filas = revelado["recursos"]
    alto_panel = 18 + len(filas) * alto_fila + 18
    estilo.panel(sup, (X_IZQ, y, ANCHO_UTIL, alto_panel))

    y_fila = y + 6
    encabezados = [col["recurso"], col["valor"], col["minimo"], col["optimo"], col["puntos"]]
    for i in range(len(encabezados)):
        estilo.texto(sup, encabezados[i], X_COLUMNAS[i], y_fila, config.LETRA_PEQUENA, config.CIAN)
    # Leyenda de la barra
    x = X_COLUMNAS[5]
    pygame.draw.rect(sup, config.ROJO, (x, y_fila, 2, 7))
    estilo.texto(sup, t["leyenda_min"], x + 5, y_fila, config.LETRA_PEQUENA, config.COLOR_TEXTO_SUAVE)
    pygame.draw.rect(sup, config.VERDE, (x + 40, y_fila, 2, 7))
    estilo.texto(sup, t["leyenda_optimo"], x + 45, y_fila, config.LETRA_PEQUENA, config.COLOR_TEXTO_SUAVE)
    y_fila = y_fila + 14

    for fila in filas:
        color = config.COLOR_ERROR if fila["bajo_minimo"] else config.COLOR_TEXTO
        celdas = [nombre_recurso(textos, fila["clave"]),
                  con_unidad(textos, fila["valor"], fila["unidad"]),
                  con_unidad(textos, fila["minimo"], fila["unidad"]),
                  con_unidad(textos, fila["optimo"], fila["unidad"]),
                  str(fila["puntos"])]
        for i in range(len(celdas)):
            estilo.texto(sup, celdas[i], X_COLUMNAS[i], y_fila + 1, config.LETRA_PEQUENA, color)
        dibujar_barra(sup, X_COLUMNAS[5], y_fila + 1, ANCHO_BARRA, fila)
        y_fila = y_fila + alto_fila

    # Fila "Budget used": % gastado, lo ahorrado y una barrita
    usado = revelado["presupuesto_usado_pct"]
    contenido = (t["presupuesto_usado"] + ": " + str(round(usado)) + "%  ("
                 + formatear_musd(revelado["ahorro_musd"]) + " " + t["ahorrado"] + ")")
    estilo.texto(sup, contenido, X_COLUMNAS[0], y_fila + 2, config.LETRA_PEQUENA, config.AMARILLO)
    pygame.draw.rect(sup, config.NEGRO, (X_COLUMNAS[5], y_fila + 3, ANCHO_BARRA, 6))
    pygame.draw.rect(sup, config.AMARILLO, (X_COLUMNAS[5], y_fila + 4,
                                            int(ANCHO_BARRA * min(1.0, usado / 100)), 4))
    return y + alto_panel


# ---------------------------------------------------------------------------
# Victoria
# ---------------------------------------------------------------------------

def dibujar_estrellas(sup, cantidad, segundos, cx, cy):
    """5 estrellas: las ganadas aparecen una por una con un pequeño "pop"."""
    for i in range(5):
        x = cx - 64 + i * 32
        aparece = 0.4 + i * 0.25                 # segundo en que aparece la estrella i
        if i < cantidad and segundos >= aparece:
            f = min(1.0, (segundos - aparece) / 0.2)
            radio = 12 * (1 + 0.5 * (1 - f))     # empieza grande y se asienta
            sprites.dibujar_estrella(sup, x, cy, radio, True)
        else:
            sprites.dibujar_estrella(sup, x, cy, 12, False)


def dibujar_victoria(sup, ui, textos, revelado):
    t = textos["resultados"]
    segundos = segundos_en_pantalla(ui)
    estilo.texto_contorno(sup, t["exito"], config.ANCHO // 2, 18, config.LETRA_TITULO, config.COLOR_OK,
                          config.NEGRO, 1)
    # Puntaje que cuenta de 0 al total en 1 s
    mostrado = int(revelado["puntaje"] * min(1.0, segundos / 1.0))
    estilo.texto(sup, t["puntaje"], X_IZQ + 4, 38, config.LETRA_PEQUENA, config.COLOR_TEXTO_SUAVE)
    estilo.texto(sup, str(mostrado), X_IZQ + 4, 48, config.LETRA_GIGANTE, config.AMARILLO)
    dibujar_estrellas(sup, revelado["estrellas"], segundos, config.ANCHO // 2, 62)

    if revelado["optimo"]:
        estilo.panel(sup, (470, 44, 150, 30), config.VERDE, config.AMARILLO)
        estilo.texto(sup, t["optimo"], 545, 59, config.LETRA_NORMAL, centrado=True)
    elif revelado["siguiente_estrella_pts"] is not None:
        aviso = t["siguiente_estrella"].replace("{pts}", str(revelado["siguiente_estrella_pts"]))
        estilo.texto(sup, aviso, config.ANCHO - X_IZQ, 58, config.LETRA_PEQUENA,
                     config.COLOR_TEXTO_SUAVE, derecha=True)

    y = dibujar_tabla(sup, textos, revelado, 90, 20)
    texto_limitado(sup, revelado["mensaje"], X_IZQ + 4, y + 8, ANCHO_UTIL - 8)


# ---------------------------------------------------------------------------
# Derrota
# ---------------------------------------------------------------------------

def dibujar_derrota(sup, ui, textos, revelado):
    t = textos["resultados"]
    if revelado["falla"]:
        titulo = traducir(t["titulos_falla"], revelado["falla"])
    else:
        titulo = t["falla_generica"]
    estilo.texto_contorno(sup, titulo, config.ANCHO // 2, 18, config.LETRA_TITULO, config.COLOR_ERROR,
                          config.NEGRO, 1)
    estilo.texto(sup, t["puntaje"] + ": 0", X_IZQ + 4, 36, config.LETRA_PEQUENA, config.COLOR_TEXTO_SUAVE)

    # 1. Recursos bajo el mínimo: "3 kg of 6 kg needed", % faltante y etiqueta
    y = 50
    estilo.texto(sup, t["fallas"] + ":", X_IZQ + 4, y, config.LETRA_PEQUENA, config.COLOR_ERROR)
    y = y + 13
    for fila in revelado["recursos"]:
        if not fila["bajo_minimo"]:
            continue
        pct = fila["faltante_pct"]
        necesarios = (t["de_necesarios"]
                      .replace("{valor}", con_unidad(textos, fila["valor"], fila["unidad"]))
                      .replace("{minimo}", con_unidad(textos, fila["minimo"], fila["unidad"])))
        estilo.texto(sup, nombre_recurso(textos, fila["clave"]) + ":", X_IZQ + 8, y, config.LETRA_PEQUENA)
        estilo.texto(sup, necesarios, 160, y, config.LETRA_PEQUENA)
        faltante = t["faltante"].replace("{pct}", str(round(pct))) + " - " + etiqueta_faltante(textos, pct)
        estilo.texto(sup, faltante, 160, y + 10, config.LETRA_PEQUENA, config.AMARILLO)
        # Barra: cuánto se tenía de lo necesario (el borde blanco es el mínimo)
        pygame.draw.rect(sup, config.NEGRO, (X_COLUMNAS[5], y + 2, ANCHO_BARRA, 8))
        pygame.draw.rect(sup, config.ROJO, (X_COLUMNAS[5], y + 3,
                                            int(ANCHO_BARRA * max(0.0, 1 - pct / 100)), 6))
        pygame.draw.rect(sup, config.BLANCO, (X_COLUMNAS[5] + ANCHO_BARRA - 1, y, 2, 12))
        y = y + 24

    # 2. Tabla que revela mínimo y óptimo de TODOS los recursos
    estilo.texto(sup, t["revelado"], X_IZQ + 4, y + 2, config.LETRA_PEQUENA, config.CIAN)
    y = dibujar_tabla(sup, textos, revelado, y + 12, 16)

    # 3. El porqué físico de cada falla (de mensajes.json)
    y = y + 6
    for falla in revelado["fallas"]:
        y = texto_limitado(sup, falla["mensaje"], X_IZQ + 4, y, ANCHO_UTIL - 8) + 4


def dibujar(sup, ui, textos):
    estilo.fondo_estrellas(sup, ui["tiempo"])
    revelado = ui["revelado"]
    if revelado["exito"]:
        dibujar_victoria(sup, ui, textos, revelado)
    else:
        dibujar_derrota(sup, ui, textos, revelado)
    return [
        Boton(textos["botones"]["reintentar"], 20, 326, 130, config.ALTO_BOTON, "reintentar",
              color=config.VERDE),
        Boton(textos["botones"]["volver_misiones"], 410, 326, 210, config.ALTO_BOTON, "volver_misiones"),
    ]
