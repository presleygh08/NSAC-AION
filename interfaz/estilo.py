# estilo.py
# El "look" 16 bits del juego: fuentes pixel, texto con sombra, paneles con borde
# pixel (estilo cuadro de diálogo de RPG) y el fondo de estrellas.

import math
import os
import random

import pygame

from interfaz import config
from interfaz.fuente_pixel import FuentePixel

# Guardamos las fuentes ya creadas para no crearlas en cada cuadro (es lento).
_fuentes = {}


def _buscar_ttf():
    """Devuelve la ruta de la primera fuente .ttf de assets/fuentes/, o None si no hay.
    (Piero agregará ahí una fuente pixel libre, con su crédito en assets/CREDITOS.md)."""
    if not os.path.isdir(config.RUTA_FUENTES):
        return None
    for nombre in sorted(os.listdir(config.RUTA_FUENTES)):
        if nombre.lower().endswith(".ttf"):
            return os.path.join(config.RUTA_FUENTES, nombre)
    return None


def fuente(tamano):
    """Fuente del tamaño pedido (la crea la primera vez).
    Si hay una .ttf en assets/fuentes/ se usa esa; si no, la fuente pixel del juego."""
    if tamano not in _fuentes:
        ruta = _buscar_ttf()
        if ruta is not None:
            _fuentes[tamano] = pygame.font.Font(ruta, tamano)
        else:
            escala = config.ESCALA_FUENTE.get(tamano, max(1, round(tamano / 8)))
            _fuentes[tamano] = FuentePixel(escala)
    return _fuentes[tamano]


def texto(sup, contenido, x, y, tamano=config.LETRA_NORMAL, color=config.COLOR_TEXTO,
          centrado=False, derecha=False, sombra=True):
    """Escribe una línea de texto SIN suavizado (antialias=False), con sombra de 1 px.
    centrado=True: (x, y) es el centro.  derecha=True: x es el borde derecho.
    Devuelve el rectángulo que ocupó el texto."""
    f = fuente(tamano)
    imagen = f.render(contenido, False, color)
    rect = imagen.get_rect()
    if centrado:
        rect.center = (x, y)
    elif derecha:
        rect.topright = (x, y)
    else:
        rect.topleft = (x, y)
    if sombra:
        imagen_sombra = f.render(contenido, False, config.COLOR_SOMBRA)
        sup.blit(imagen_sombra, (rect.x + 1, rect.y + 1))
    sup.blit(imagen, rect)       # blit = "pegar" la imagen en la superficie
    return rect


def texto_contorno(sup, contenido, x, y, tamano, color, color_contorno=config.NEGRO, grosor=2):
    """Texto centrado en (x, y) con contorno de 'grosor' píxeles (títulos tipo arcade)."""
    for dx in range(-grosor, grosor + 1):
        for dy in range(-grosor, grosor + 1):
            if dx != 0 or dy != 0:
                texto(sup, contenido, x + dx, y + dy, tamano, color_contorno, centrado=True, sombra=False)
    return texto(sup, contenido, x, y, tamano, color, centrado=True, sombra=False)


def partir_lineas(contenido, ancho_max, tamano=config.LETRA_NORMAL):
    """Parte un texto largo en líneas que no pasen de ancho_max píxeles.
    Respeta los saltos de línea que ya trae el texto ("\\n")."""
    f = fuente(tamano)
    lineas = []
    for parrafo in contenido.split("\n"):
        linea = ""
        for palabra in parrafo.split(" "):
            prueba = palabra if linea == "" else linea + " " + palabra
            if f.size(prueba)[0] > ancho_max and linea != "":
                lineas.append(linea)
                linea = palabra
            else:
                linea = prueba
        lineas.append(linea)
    return lineas


def texto_multilinea(sup, contenido, x, y, ancho_max, tamano=config.LETRA_NORMAL,
                     color=config.COLOR_TEXTO):
    """Escribe un texto largo en varias líneas. Devuelve la y donde terminó."""
    alto_linea = fuente(tamano).get_linesize()
    for linea in partir_lineas(contenido, ancho_max, tamano):
        texto(sup, linea, x, y, tamano, color)
        y = y + alto_linea
    return y


def panel(sup, rect, color_fondo=config.COLOR_PANEL, color_borde=config.COLOR_BORDE):
    """Panel con borde pixel: sombra de 1 px, marco de 2 px y esquinas "en escalón"
    (se recorta 1 píxel en cada esquina para que no se vea redondeado ni cuadrado)."""
    r = pygame.Rect(rect)
    # 1. Sombra abajo a la derecha
    pygame.draw.rect(sup, config.COLOR_SOMBRA, r.move(1, 1))
    # 2. Marco exterior (color del borde) con esquinas recortadas
    pygame.draw.rect(sup, color_borde, (r.x + 1, r.y, r.w - 2, r.h))
    pygame.draw.rect(sup, color_borde, (r.x, r.y + 1, r.w, r.h - 2))
    # 3. Relleno, dejando 2 px de marco
    pygame.draw.rect(sup, color_fondo, r.inflate(-4, -4))


# --- Fondo de estrellas que parpadean ---
_estrellas = []


def _crear_estrellas():
    azar = random.Random(7)          # siempre las mismas estrellas
    for _ in range(90):
        x = azar.randrange(config.ANCHO)
        y = azar.randrange(config.ALTO)
        fase = azar.random() * 6.28  # cada estrella parpadea a su ritmo
        _estrellas.append((x, y, fase))


def fondo_estrellas(sup, tiempo):
    """Pinta el fondo azul marino con estrellas que parpadean suavemente.
    tiempo: segundos desde que empezó el juego."""
    if not _estrellas:
        _crear_estrellas()
    sup.fill(config.COLOR_FONDO)
    for (x, y, fase) in _estrellas:
        brillo = 0.5 + 0.5 * math.sin(tiempo * 2 + fase)    # entre 0 y 1
        if brillo > 0.75:
            color = config.BLANCO
        elif brillo > 0.35:
            color = config.GRIS_CLARO
        else:
            color = config.GRIS
        sup.set_at((x, y), color)
