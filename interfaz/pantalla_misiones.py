# pantalla_misiones.py
# "Choose your mission": lista de misiones a la derecha y previsualización a la izquierda.
# Los datos salen de nucleo.cargar_misiones(progreso) (nunca trae mínimos ni óptimos).
# Al pasar el mouse o clicar una fila se actualiza la previsualización.

import pygame

import nucleo
from interfaz import config, estilo, imagenes, sprites
from interfaz.componentes import (Boton, formatear_musd, nombre_destino, nombre_dificultad, nombre_mision,
                                  posicion_mouse,
                                  traducir)

X_LISTA = 300
Y_LISTA = 62
ALTO_FILA = 44


def fila_a_mostrar(ui, parrilla):
    """La misión de la previsualización: la que está bajo el mouse, o la elegida,
    o la primera."""
    mouse = posicion_mouse()
    for i in range(len(parrilla)):
        rect = pygame.Rect(X_LISTA, Y_LISTA + i * ALTO_FILA, 320, ALTO_FILA - 6)
        if rect.collidepoint(mouse):
            return parrilla[i]
    for fila in parrilla:
        if fila["id"] == ui["mision_vista"]:
            return fila
    return parrilla[0]


def dibujar_fila(sup, textos, fila, y, elegida):
    """Una fila: nombre, etiqueta de dificultad con color y estado."""
    t = textos["misiones"]
    rect = pygame.Rect(X_LISTA, y, 320, ALTO_FILA - 6)
    bloqueada = fila["estado"] in ("bloqueada", "proximamente")
    if elegida:
        borde = config.AMARILLO
    else:
        borde = config.COLOR_BORDE
    if bloqueada:
        fondo = config.GRIS_OSCURO
    else:
        fondo = config.COLOR_PANEL
    estilo.panel(sup, rect, fondo, borde)

    color_texto = config.COLOR_TEXTO_SUAVE if bloqueada else config.COLOR_TEXTO
    estilo.texto_ajustado(sup, nombre_mision(textos, fila["id"], fila["nombre"]), rect.x + 8, rect.y + 5,
                          rect.w - 16, config.LETRA_NORMAL, color_texto)
    # Etiqueta de dificultad (gris si está bloqueada)
    color_dif = config.COLORES_DIFICULTAD.get(fila["dificultad"], config.BLANCO)
    if bloqueada:
        color_dif = config.GRIS
    estilo.texto(sup, nombre_dificultad(textos, fila["dificultad"]), rect.x + 8, rect.y + 25,
                 config.LETRA_PEQUENA, color_dif)

    # Estado abajo a la derecha (en la misma línea que la dificultad, para no chocar
    # con los nombres largos de arriba).
    x_derecha = rect.right - 8
    y_estado = rect.y + 25
    if fila["estado"] == "completada":
        for i in range(5):
            sprites.dibujar_estrella(sup, x_derecha - 62 + i * 14, y_estado + 5, 5, i < fila["estrellas"])
        estilo.texto(sup, t["mejor_puntaje"] + ": " + str(fila["mejor_puntaje"]), x_derecha - 72,
                     y_estado, config.LETRA_PEQUENA, config.AMARILLO, derecha=True)
    elif fila["estado"] == "bloqueada":
        sprites.dibujar_candado(sup, x_derecha - 64, y_estado - 1)
        estilo.texto(sup, t["estados"]["bloqueada"], x_derecha, y_estado, config.LETRA_PEQUENA,
                     config.GRIS_CLARO, derecha=True)
    else:
        estilo.texto(sup, traducir(t["estados"], fila["estado"]), x_derecha, y_estado,
                     config.LETRA_PEQUENA, color_texto, derecha=True)


def dibujar_previsualizacion(sup, ui, textos, fila):
    """Panel izquierdo: foto pixelada de la misión real (o placeholder), destino,
    cohete y presupuesto."""
    t = textos["misiones"]
    estilo.panel(sup, (20, 62, 260, 236))
    imagenes.dibujar_imagen_mision(sup, (30, 72, 240, 130), fila["id"], fila["destino"],
                                   nombre_mision(textos, fila["id"], fila["nombre"]), ui["tiempo"])
    estilo.texto_ajustado(sup, nombre_mision(textos, fila["id"], fila["nombre"]), 30, 210, 244,
                          config.LETRA_NORMAL, config.AMARILLO)
    estilo.texto(sup, t["destino"] + ": " + nombre_destino(textos, fila["destino"]), 30, 232,
                 config.LETRA_PEQUENA)
    estilo.texto(sup, t["cohete"] + ": " + str(fila["cohete"]), 30, 250, config.LETRA_PEQUENA)
    if fila["presupuesto_musd"] is not None:
        estilo.texto(sup, t["presupuesto"] + ": " + formatear_musd(fila["presupuesto_musd"]),
                     30, 268, config.LETRA_PEQUENA)


def dibujar(sup, ui, textos):
    t = textos["misiones"]
    estilo.fondo_estrellas(sup, ui["tiempo"])
    estilo.texto(sup, t["titulo"], config.ANCHO // 2, 20, config.LETRA_TITULO, config.AMARILLO,
                 centrado=True)
    estilo.texto(sup, t["ayuda"], config.ANCHO // 2, 44, config.LETRA_PEQUENA,
                 config.COLOR_TEXTO_SUAVE, centrado=True)

    parrilla = nucleo.cargar_misiones(ui["progreso"])
    if ui["mision_vista"] is None:
        ui["mision_vista"] = parrilla[0]["id"]

    botones = []
    y = Y_LISTA
    for fila in parrilla:
        dibujar_fila(sup, textos, fila, y, fila["id"] == ui["mision_vista"])
        # Zona invisible para clicar la fila (elige la misión para la previsualización).
        botones.append(Boton("", X_LISTA, y, 320, ALTO_FILA - 6, "ver_mision", fila["id"],
                             visible=False))
        y = y + ALTO_FILA

    dibujar_previsualizacion(sup, ui, textos, fila_a_mostrar(ui, parrilla))

    se_puede = nucleo.puede_jugar(ui["progreso"], ui["mision_vista"])
    botones.append(Boton(textos["botones"]["atras"], 20, 316, 100, config.ALTO_BOTON, "ir_avatar"))
    botones.append(Boton(textos["botones"]["siguiente"], 520, 316, 100, config.ALTO_BOTON,
                         "ir_info", activo=se_puede, color=config.VERDE, principal=True))
    return botones
