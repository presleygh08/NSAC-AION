# notificaciones.py
# Cuadro de notificaciones del asistente (sección 7.3 de la especificación).
#
# Uso desde cualquier parte del juego:
#     notificaciones.mostrar_notificacion(ui, "Texto en inglés", "feliz")
# El mensaje entra en una cola (ui["notificaciones"]) y se muestra en un cuadro abajo al
# centro que sube deslizándose, con el retrato del NPC con esa expresión y el texto que
# se va escribiendo letra por letra. Se va solo después de unos segundos, o antes con un
# clic sobre el cuadro o con Enter. Después aparece el siguiente de la cola.
# No bloquea la pantalla: el resto de botones sigue funcionando.
#
# El estado vive en el diccionario "ui" (regla del proyecto), por eso las funciones lo reciben.

import pygame

from interfaz import config, estilo, sprites
from interfaz.componentes import Boton

CAJA = pygame.Rect(130, 304, 380, 48)   # entre los botones BACK y NEXT de los menús
ENTRADA = 0.3                           # segundos que tarda en subir
SALIDA = 0.3                            # segundos que tarda en bajar
LETRAS_POR_SEGUNDO = 45


def mostrar_notificacion(ui, texto, expresion="feliz", duracion=None):
    """Agrega un mensaje a la cola. expresion: una de sprites.EXPRESIONES_NPC.
    {nombre} en el texto se cambia por el callsign del jugador."""
    if duracion is None:
        duracion = config.DURACION_NOTIFICACION
    texto = texto.replace("{nombre}", ui["jugador"]["nombre"])
    if "notificaciones" not in ui:
        ui["notificaciones"] = []
    ui["notificaciones"].append({"texto": texto, "expresion": expresion, "duracion": duracion,
                                 "t0": None, "fin": None})


def actual(ui):
    """La notificación que se está mostrando (o None). Si no hay ninguna, toma la
    siguiente de la cola; si la actual ya terminó de salir, la quita."""
    cola = ui.get("notificaciones", [])
    if not cola:
        return None
    nota = cola[0]
    if nota["t0"] is None:                       # recién empieza a mostrarse
        nota["t0"] = ui["tiempo"]
        nota["fin"] = nota["t0"] + ENTRADA + nota["duracion"]
    if ui["tiempo"] >= nota["fin"] + SALIDA:     # ya salió del todo: la siguiente
        cola.pop(0)
        return actual(ui)
    return nota


def hay_notificacion(ui):
    return actual(ui) is not None


def cerrar(ui):
    """Cierra la notificación actual (empieza a bajar ya)."""
    nota = actual(ui)
    if nota is not None and ui["tiempo"] < nota["fin"]:
        nota["fin"] = ui["tiempo"]


def dibujar(sup, ui, textos):
    """Dibuja la notificación actual encima de la pantalla. Devuelve su botón (invisible)
    para cerrarla con un clic, o una lista vacía."""
    nota = actual(ui)
    if nota is None:
        return []
    ahora = ui["tiempo"]
    # Cuánto se ve el cuadro: sube al entrar, baja al salir
    if ahora < nota["t0"] + ENTRADA:
        visible = (ahora - nota["t0"]) / ENTRADA
    elif ahora > nota["fin"]:
        visible = max(0.0, 1 - (ahora - nota["fin"]) / SALIDA)
    else:
        visible = 1.0
    caja = CAJA.copy()
    caja.y = int(config.ALTO - (config.ALTO - CAJA.y) * visible)

    estilo.panel(sup, caja, config.COLOR_PANEL, config.AMARILLO)
    sprites.dibujar_npc(sup, caja.x + 8, caja.y + 8, nota["expresion"])
    # Texto letra por letra
    letras = int((ahora - nota["t0"] - ENTRADA) * LETRAS_POR_SEGUNDO)
    contenido = nota["texto"][:max(0, letras)]
    estilo.texto_multilinea(sup, contenido, caja.x + 48, caja.y + 7, caja.w - 64, config.LETRA_PEQUENA)
    estilo.texto(sup, "x", caja.right - 9, caja.y + 6, config.LETRA_PEQUENA, config.COLOR_TEXTO_SUAVE)
    return [Boton("", caja.x, caja.y, caja.w, caja.h, "cerrar_notificacion", visible=False)]
