# resultados.py
# Pantalla de resultados (sección 6 de la especificación, con los cambios de la v2, D3).
# Todo sale de nucleo.revelar(estado), que app.py guarda en ui["revelado"]
# (y llama a registrar_resultado una sola vez al entrar; ui["resultados_t0"] es el
# segundo en que se entró, para las animaciones).
#
# Regla D3: NUNCA se muestran cifras de mínimo ni óptimo, salvo con 5 estrellas.
#   Victoria con 5 estrellas: tabla completa (tu valor, mínimo, óptimo, puntos y barra).
#   Victoria con menos:       por recurso, tu valor, una barra con zonas de color
#                             (rojo = bajo el mínimo, amarillo = aceptable, verde = cerca del
#                             óptimo, naranja = de más) con la marca de tu valor, y la pista
#                             ("Needs a bit more", "Close to optimal"...). Zona y pista las da revelar.
#   Derrota:                  título rojo con la falla principal, la misma tabla sin cifras
#                             (los recursos bajo el mínimo en rojo) y la frase de AION de cada
#                             falla (los mensajes de mensajes.json NO se muestran: traen el mínimo).

import pygame

from interfaz import config, estilo, sprites
from interfaz.componentes import (Boton, formatear_musd, formatear_numero, nombre_recurso,
                                  traducir, unidad_recurso)

X_IZQ = 20
ANCHO_UTIL = config.ANCHO - 2 * X_IZQ
# Columnas de la tabla completa (5 estrellas): recurso, tu valor, mínimo, óptimo, puntos, barra
X_COLUMNAS = [28, 186, 264, 336, 412, 462]
ANCHO_BARRA = 148
# Columnas de la tabla sin cifras: recurso, tu valor, pista, barra con zonas
X_COLUMNAS_PARCIAL = [28, 186, 270, 400]
ANCHO_BARRA_PARCIAL = 210
Y_LIMITE = 318            # nada de texto por debajo (ahí van los botones)


# ---------------------------------------------------------------------------
# Ayudas
# ---------------------------------------------------------------------------

def segundos_en_pantalla(ui):
    return ui["tiempo"] - ui.get("resultados_t0", ui["tiempo"])


def con_unidad(textos, fila, numero):
    return formatear_numero(numero) + " " + unidad_recurso(textos, fila["clave"], fila["unidad"])


def dibujar_barra(sup, x, y, ancho, fila):
    """Barra de la tabla completa (5 estrellas): tu valor relleno, marca roja en el mínimo
    y marca verde en el óptimo."""
    tope = max(fila["optimo"] * 1.4, fila["valor"], fila["minimo"]) * 1.05
    pygame.draw.rect(sup, config.NEGRO, (x, y, ancho, 8))
    color = config.COLOR_ERROR if fila["bajo_minimo"] else config.COLOR_OK
    largo = int(ancho * min(1.0, fila["valor"] / tope))
    pygame.draw.rect(sup, color, (x, y + 1, largo, 6))
    for valor, color_marca in ((fila["minimo"], config.ROJO), (fila["optimo"], config.VERDE)):
        xm = x + int(ancho * valor / tope)
        pygame.draw.rect(sup, config.BLANCO, (xm - 1, y - 3, 3, 14))     # borde para que se vea
        pygame.draw.rect(sup, color_marca, (xm, y - 2, 1, 12))


def dibujar_barra_zonas(sup, x, y, ancho, fila):
    """Barra SIN cifras (D3): cuatro zonas de color y una marca blanca en tu valor.
    Los límites de las zonas se calculan con el mínimo y el óptimo, pero no se escriben."""
    optimo = fila["optimo"]
    tope = max(optimo * 1.4, fila["valor"] * 1.05)
    limites = [0, fila["minimo"], optimo * 0.9, optimo * 1.1, tope]
    colores = [config.COLORES_ZONA["bajo_minimo"], config.COLORES_ZONA["aceptable"],
               config.COLORES_ZONA["optimo"], config.COLORES_ZONA["exceso"]]
    pygame.draw.rect(sup, config.NEGRO, (x - 1, y - 1, ancho + 2, 10))
    for i in range(4):
        x1 = x + int(ancho * min(limites[i], tope) / tope)
        x2 = x + int(ancho * min(limites[i + 1], tope) / tope)
        if x2 > x1:
            pygame.draw.rect(sup, colores[i], (x1, y, x2 - x1, 8))
    xm = x + int(ancho * min(fila["valor"], tope) / tope)
    xm = max(x + 1, min(x + ancho - 2, xm))
    pygame.draw.rect(sup, config.NEGRO, (xm - 2, y - 4, 5, 16))          # marca de tu valor
    pygame.draw.rect(sup, config.BLANCO, (xm - 1, y - 3, 3, 14))


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


def dibujar_fila_presupuesto(sup, textos, revelado, x_barra, ancho_barra, y_fila):
    """Fila "Budget used": % gastado, lo ahorrado y una barrita (se revela después de la misión)."""
    t = textos["resultados"]
    usado = revelado["presupuesto_usado_pct"]
    contenido = (t["presupuesto_usado"] + ": " + str(round(usado)) + "%  ("
                 + formatear_musd(revelado["ahorro_musd"]) + " " + t["ahorrado"] + ")")
    estilo.texto(sup, contenido, X_COLUMNAS[0], y_fila + 2, config.LETRA_PEQUENA, config.AMARILLO)
    pygame.draw.rect(sup, config.NEGRO, (x_barra, y_fila + 3, ancho_barra, 6))
    pygame.draw.rect(sup, config.AMARILLO, (x_barra, y_fila + 4,
                                            int(ancho_barra * min(1.0, usado / 100)), 4))


# ---------------------------------------------------------------------------
# Tablas
# ---------------------------------------------------------------------------

def dibujar_tabla(sup, textos, revelado, y, alto_fila):
    """Tabla COMPLETA con cifras (solo con 5 estrellas, D3) y la fila "Budget used".
    Devuelve la y donde terminó."""
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
                  con_unidad(textos, fila, fila["valor"]),
                  con_unidad(textos, fila, fila["minimo"]),
                  con_unidad(textos, fila, fila["optimo"]),
                  str(fila["puntos"])]
        for i in range(len(celdas)):
            estilo.texto(sup, celdas[i], X_COLUMNAS[i], y_fila + 1, config.LETRA_PEQUENA, color)
        dibujar_barra(sup, X_COLUMNAS[5], y_fila + 1, ANCHO_BARRA, fila)
        y_fila = y_fila + alto_fila

    dibujar_fila_presupuesto(sup, textos, revelado, X_COLUMNAS[5], ANCHO_BARRA, y_fila)
    return y + alto_panel


def dibujar_tabla_sin_cifras(sup, textos, revelado, y, alto_fila):
    """Tabla SIN mínimos ni óptimos (D3): recurso, tu valor, pista y barra con zonas.
    Los recursos bajo el mínimo van en rojo. Devuelve la y donde terminó."""
    t = textos["resultados"]
    col = t["columnas"]
    filas = revelado["recursos"]
    alto_panel = 18 + len(filas) * alto_fila + 18
    estilo.panel(sup, (X_IZQ, y, ANCHO_UTIL, alto_panel))

    y_fila = y + 6
    encabezados = [col["recurso"], col["valor"], col["pista"]]
    for i in range(len(encabezados)):
        estilo.texto(sup, encabezados[i], X_COLUMNAS_PARCIAL[i], y_fila, config.LETRA_PEQUENA, config.CIAN)
    y_fila = y_fila + 14

    for fila in filas:
        color = config.COLOR_ERROR if fila["bajo_minimo"] else config.COLOR_TEXTO
        estilo.texto(sup, nombre_recurso(textos, fila["clave"]), X_COLUMNAS_PARCIAL[0], y_fila + 1,
                     config.LETRA_PEQUENA, color)
        estilo.texto(sup, con_unidad(textos, fila, fila["valor"]), X_COLUMNAS_PARCIAL[1], y_fila + 1,
                     config.LETRA_PEQUENA, color)
        estilo.texto(sup, fila["pista"], X_COLUMNAS_PARCIAL[2], y_fila + 1, config.LETRA_PEQUENA,
                     config.COLORES_ZONA[fila["zona"]])
        dibujar_barra_zonas(sup, X_COLUMNAS_PARCIAL[3], y_fila + 1, ANCHO_BARRA_PARCIAL, fila)
        y_fila = y_fila + alto_fila

    dibujar_fila_presupuesto(sup, textos, revelado, X_COLUMNAS_PARCIAL[3], ANCHO_BARRA_PARCIAL, y_fila)
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

    if revelado["estrellas"] >= 5:
        # 5 estrellas: recién aquí se revelan las cifras exactas (D3)
        y = dibujar_tabla(sup, textos, revelado, 90, 20)
    else:
        estilo.texto(sup, t["revelado_parcial"], X_IZQ + 4, 80, config.LETRA_PEQUENA, config.CIAN)
        y = dibujar_tabla_sin_cifras(sup, textos, revelado, 92, 20)
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

    # 1. Tabla sin cifras de mínimo ni óptimo (D3): solo zona y pista de cada recurso
    estilo.texto(sup, t["revelado_parcial"], X_IZQ + 4, 50, config.LETRA_PEQUENA, config.CIAN)
    y = dibujar_tabla_sin_cifras(sup, textos, revelado, 62, 18)

    # 2. Qué pasó: la frase de AION de cada falla (sin números), con su retrato
    frases = textos["simulacion"]["frases"]
    vistas = []
    y = y + 8
    sprites.dibujar_npc(sup, X_IZQ + 4, y, "preocupado")
    for falla in revelado["fallas"]:
        frase = frases.get(falla["falla"], t["falla_generica"])
        if frase in vistas:                  # sin_ciencia y fuera_de_tiempo comparten frase
            continue
        vistas.append(frase)
        y = texto_limitado(sup, frase, X_IZQ + 44, y, ANCHO_UTIL - 48) + 4


def dibujar(sup, ui, textos):
    estilo.fondo_estrellas(sup, ui["tiempo"])
    revelado = ui["revelado"]
    if revelado["exito"]:
        dibujar_victoria(sup, ui, textos, revelado)
    else:
        dibujar_derrota(sup, ui, textos, revelado)
    return [
        Boton(textos["botones"]["reintentar"], 20, 326, 130, config.ALTO_BOTON, "reintentar",
              color=config.VERDE, principal=True),
        Boton(textos["botones"]["volver_misiones"], 410, 326, 210, config.ALTO_BOTON, "volver_misiones"),
    ]
