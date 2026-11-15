# imagenes.py
# Fotos de las misiones (sección 8 de la especificación), con efecto 16 bits.
# Las fotos están en assets/misiones/<id_mision>.png (fotos de NASA de dominio
# público, con su crédito en assets/CREDITOS.md). Al cargarlas:
#   1. se recortan al centro con la forma (proporción) del recuadro donde se dibujan,
#   2. se reducen a unos 120x80 píxeles (así se ven los "pixeles gordos"),
#   3. cada píxel se cambia por el color más parecido de la paleta del juego,
#   4. se agrandan otra vez SIN suavizado al tamaño del recuadro.
# El resultado se guarda en una caché: el cálculo se hace una sola vez por tamaño.

import os

import pygame

from interfaz import config, sprites

PIXELES_REDUCIDOS = 120 * 80     # ~9600 píxeles, como pide la especificación

_cache = {}           # (mision_id, ancho, alto) -> Surface o None
_color_cercano = {}   # color (reducido) -> color de la paleta (para no recalcularlo)


def color_mas_cercano(color):
    """Color de config.PALETA más parecido a 'color' (distancia en rojo, verde, azul)."""
    r, g, b = color[0], color[1], color[2]
    clave = (r // 4, g // 4, b // 4)      # colores casi iguales comparten resultado
    if clave in _color_cercano:
        return _color_cercano[clave]
    mejor = config.PALETA[0]
    mejor_distancia = None
    for c in config.PALETA:
        distancia = (r - c[0]) ** 2 + (g - c[1]) ** 2 + (b - c[2]) ** 2
        if mejor_distancia is None or distancia < mejor_distancia:
            mejor = c
            mejor_distancia = distancia
    _color_cercano[clave] = mejor
    return mejor


def recortar_al_centro(foto, ancho, alto):
    """Recorta la foto al centro para que tenga la misma proporción que ancho x alto."""
    fw, fh = foto.get_size()
    if fw / fh > ancho / alto:
        # La foto es más ancha que el recuadro: quitamos de los lados.
        nuevo_ancho = int(fh * ancho / alto)
        rect = pygame.Rect((fw - nuevo_ancho) // 2, 0, nuevo_ancho, fh)
    else:
        # La foto es más alta: quitamos de arriba y abajo.
        nuevo_alto = int(fw * alto / ancho)
        rect = pygame.Rect(0, (fh - nuevo_alto) // 2, fw, nuevo_alto)
    return foto.subsurface(rect)


def pixelar(foto, ancho, alto):
    """Aplica los pasos 1 a 4 y devuelve una Surface de ancho x alto."""
    recorte = recortar_al_centro(foto, ancho, alto)
    # Tamaño reducido con la misma proporción y ~PIXELES_REDUCIDOS píxeles.
    ancho_chico = max(8, int((PIXELES_REDUCIDOS * ancho / alto) ** 0.5))
    alto_chico = max(8, int(ancho_chico * alto / ancho))
    # smoothscale promedia los colores al achicar (necesita una imagen de 24 o 32 bits,
    # como las fotos PNG/JPG normales).
    chica = pygame.transform.smoothscale(recorte, (ancho_chico, alto_chico))
    for y in range(alto_chico):
        for x in range(ancho_chico):
            chica.set_at((x, y), color_mas_cercano(chica.get_at((x, y))))
    return pygame.transform.scale(chica, (ancho, alto))


def ruta_imagen(mision_id):
    return os.path.join(config.RUTA_IMAGENES_MISIONES, mision_id + ".png")


def imagen_mision(mision_id, ancho, alto):
    """Foto pixelada de la misión del tamaño pedido, o None si no hay foto
    (entonces la pantalla dibuja el placeholder de sprites.dibujar_destino)."""
    clave = (mision_id, ancho, alto)
    if clave not in _cache:
        ruta = ruta_imagen(mision_id)
        if os.path.exists(ruta):
            try:
                _cache[clave] = pixelar(pygame.image.load(ruta), ancho, alto)
            except pygame.error:
                _cache[clave] = None       # archivo dañado: usamos el placeholder
        else:
            _cache[clave] = None
    return _cache[clave]


def dibujar_imagen_mision(sup, rect, mision_id, destino, nombre, tiempo):
    """Dibuja la foto pixelada en 'rect', o el placeholder si no hay foto."""
    r = pygame.Rect(rect)
    imagen = imagen_mision(mision_id, r.w, r.h)
    if imagen is not None:
        sup.blit(imagen, r)
    else:
        sprites.dibujar_destino(sup, r, destino, tiempo, nombre)
