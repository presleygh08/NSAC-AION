# pausa.py
# Menú de pausa (v2, punto 4). Se abre con Esc en el laboratorio (si no hay una ventana
# abierta) y en la pantalla didáctica. Mientras está abierto, el avatar no se mueve y
# solo funcionan estos botones:
#   Resume            -> cierra el menú (también Esc o Enter)
#   Restart mission   -> la misma misión desde CML 1, sin conservar nada
#   Back to missions  -> la parrilla de misiones
#   Main menu         -> la pantalla de inicio (el progreso se mantiene)
#   Language / Idioma -> cambia entre inglés y español al instante (v3, E; lo hace app.py)
# El estado es ui["pausa"] (True / False). Las acciones que cambian de pantalla las
# termina app.py (empezar_mision, ir_a_misiones...).

import pygame

from interfaz import config
from interfaz.componentes import Boton, dibujar_ventana

VENTANA = pygame.Rect(190, 74, 260, 212)
ANCHO_BOTON = 220

# (clave del texto en textos_en.json -> "pausa", acción, color)
OPCIONES = [
    ("reanudar", "pausa_reanudar", config.VERDE),
    ("reiniciar", "pausa_reiniciar", config.COLOR_BOTON),
    ("misiones", "pausa_misiones", config.COLOR_BOTON),
    ("menu", "pausa_menu", config.COLOR_BOTON),
    ("idioma", "pausa_idioma", config.CIAN_OSCURO),      # v3 (E): Language / Idioma
]


def dibujar(sup, ui, textos):
    """Oscurece la pantalla y dibuja el menú. Devuelve sus botones."""
    t = textos["pausa"]
    y = dibujar_ventana(sup, VENTANA, t["titulo"], config.AMARILLO)
    botones = []
    for clave, accion, color in OPCIONES:
        if clave == "idioma":
            # "Language / Idioma: EN" (o ES): el mismo texto en los dos idiomas
            etiqueta = textos["idioma"]["etiqueta"] + ": " + textos["idioma"][ui["idioma"]]
        else:
            etiqueta = t[clave]
        # "Resume" es el botón principal: Enter lo activa.
        botones.append(Boton(etiqueta, VENTANA.centerx - ANCHO_BOTON // 2, y + 2, ANCHO_BOTON,
                             config.ALTO_BOTON, accion, color=color,
                             principal=(accion == "pausa_reanudar")))
        y = y + config.ALTO_BOTON + 8
    return botones


def aplicar(ui, accion):
    """Acciones del menú. Cualquier opción cierra el menú. Devuelve True si ya no hay
    nada más que hacer (Resume); False si app.py debe terminar la acción."""
    if not accion.startswith("pausa_"):
        return False
    ui["pausa"] = False
    return accion == "pausa_reanudar"
