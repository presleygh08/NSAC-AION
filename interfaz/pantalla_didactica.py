# pantalla_didactica.py
# Pantalla didáctica con AION (v2, punto 3). Va entre la ficha de la misión (RUN) y el
# laboratorio. Todos los textos salen de interfaz/guia_misiones_en.json (textos["guia"]):
#   Izquierda: AION, "Mission briefing with AION", la introducción, en qué misión real se
#              inspira, el dato del cohete y la regla del presupuesto.
#   Derecha:   una tarjeta por recurso de la misión (nombre, unidad, qué es, por qué importa
#              y la referencia de "pistas_referencia"), 2 por página con flechas ◀ ▶.
# Botón LET'S DESIGN (o Enter) -> laboratorio. Esc -> menú de pausa.
#
# Qué recursos tiene la misión sale de nucleo.recursos_visibles (pantalla_info.datos_ficha),
# nunca de los mínimos ni los óptimos.

import pygame

from interfaz import config, estilo, pantalla_info, sprites
from interfaz.componentes import (Boton, info_mision, info_recurso, nombre_recurso,
                                  unidad_recurso)

PANEL_IZQ = pygame.Rect(12, 30, 248, 284)
PANEL_DER = pygame.Rect(268, 30, 360, 284)
POR_PAGINA = 2
ALTO_TARJETA = 132


def cantidad_paginas(claves):
    return (len(claves) + POR_PAGINA - 1) // POR_PAGINA      # división redondeando hacia arriba


def pagina_actual(ui, claves):
    """Página que se ve (se corrige si quedó fuera de rango)."""
    total = cantidad_paginas(claves)
    pagina = max(0, min(ui["pagina_didactica"], total - 1))
    ui["pagina_didactica"] = pagina
    return pagina


def dibujar_aion_grande(sup, x, y, tiempo):
    """AION al doble de tamaño (64x64), sin suavizar."""
    retrato = pygame.Surface((32, 32))
    sprites.dibujar_aion(retrato, 0, 0, "feliz", tiempo)
    sup.blit(pygame.transform.scale(retrato, (64, 64)), (x, y))


def dibujar_izquierda(sup, ui, textos, mision):
    guia = textos["guia"]["pantalla_didactica"]
    estilo.panel(sup, PANEL_IZQ)
    x = PANEL_IZQ.x + 10
    ancho = PANEL_IZQ.w - 20
    dibujar_aion_grande(sup, x, PANEL_IZQ.y + 10, ui["tiempo"])
    estilo.texto(sup, textos["laboratorio"]["npc_nombre"], x + 32, PANEL_IZQ.y + 78,
                 config.LETRA_PEQUENA, config.CIAN, centrado=True)
    # Al lado de AION: su introducción, como un globo de diálogo
    estilo.texto_multilinea(sup, guia["intro"], x + 74, PANEL_IZQ.y + 14, ancho - 74,
                            config.LETRA_PEQUENA)

    y = PANEL_IZQ.y + 92
    y = estilo.texto_multilinea(sup, ui["mision_nombre"], x, y, ancho, config.LETRA_NORMAL,
                                config.AMARILLO) + 4
    y = estilo.texto_multilinea(sup, mision.get("inspirada_en", ""), x, y, ancho, config.LETRA_PEQUENA,
                                config.CIAN) + 6
    y = estilo.texto_multilinea(sup, mision.get("cohete", ""), x, y, ancho, config.LETRA_PEQUENA) + 6
    estilo.texto_multilinea(sup, guia["regla_presupuesto"], x, y, ancho, config.LETRA_PEQUENA,
                            config.VERDE)


def dibujar_tarjeta(sup, textos, mision, clave, unidad_datos, y):
    """Tarjeta de un recurso: nombre (unidad), qué es, por qué importa y la referencia."""
    rect = pygame.Rect(PANEL_DER.x + 8, y, PANEL_DER.w - 16, ALTO_TARJETA - 6)
    estilo.panel(sup, rect, config.AZUL_PANEL, config.COLOR_BORDE)
    x = rect.x + 8
    ancho = rect.w - 16
    info = info_recurso(textos, clave)
    titulo = nombre_recurso(textos, clave) + " (" + unidad_recurso(textos, clave, unidad_datos) + ")"
    estilo.texto(sup, titulo, x, rect.y + 6, config.LETRA_PEQUENA, config.AMARILLO)
    yy = rect.y + 20
    yy = estilo.texto_multilinea(sup, info.get("que_es", ""), x, yy, ancho, config.LETRA_PEQUENA) + 3
    yy = estilo.texto_multilinea(sup, info.get("por_que_importa", ""), x, yy, ancho, config.LETRA_PEQUENA,
                                 config.COLOR_TEXTO_SUAVE) + 3
    referencia = mision.get("pistas_referencia", {}).get(clave)
    if referencia:
        estilo.texto_multilinea(sup, textos["didactica"]["referencia"] + ": " + referencia, x, yy, ancho,
                                config.LETRA_PEQUENA, config.VERDE)


def dibujar(sup, ui, textos):
    t = textos["didactica"]
    estilo.fondo_estrellas(sup, ui["tiempo"])
    guia = textos["guia"]["pantalla_didactica"]
    estilo.texto(sup, guia["titulo"], config.ANCHO // 2, 15, config.LETRA_NORMAL, config.AMARILLO,
                 centrado=True)

    ficha = pantalla_info.datos_ficha(ui)          # claves y unidades de los recursos (sin mínimos)
    claves = ficha["claves"]
    mision = info_mision(textos, ui["mision_id"])
    dibujar_izquierda(sup, ui, textos, mision)

    # Derecha: tarjetas de la página actual
    estilo.panel(sup, PANEL_DER)
    pagina = pagina_actual(ui, claves)
    total = cantidad_paginas(claves)
    estilo.texto(sup, t["recursos"], PANEL_DER.x + 10, PANEL_DER.y + 6, config.LETRA_PEQUENA, config.CIAN)
    y = PANEL_DER.y + 20
    for clave in claves[pagina * POR_PAGINA:(pagina + 1) * POR_PAGINA]:
        dibujar_tarjeta(sup, textos, mision, clave, ficha["unidades"][clave], y)
        y = y + ALTO_TARJETA

    botones = []
    if total > 1:
        texto_pagina = t["pagina"].replace("{n}", str(pagina + 1)).replace("{total}", str(total))
        estilo.texto(sup, texto_pagina, PANEL_DER.right - 40, PANEL_DER.y + 6, config.LETRA_PEQUENA,
                     config.COLOR_TEXTO_SUAVE, derecha=True)
        botones.append(Boton("", PANEL_DER.right - 34, PANEL_DER.y + 3, 13, 13, "pagina_didactica", -1,
                             activo=pagina > 0, icono="izquierda"))
        botones.append(Boton("", PANEL_DER.right - 18, PANEL_DER.y + 3, 13, 13, "pagina_didactica", 1,
                             activo=pagina < total - 1, icono="derecha"))

    botones.append(Boton(textos["botones"]["atras"], 12, 324, 100, config.ALTO_BOTON, "volver_info"))
    botones.append(Boton(guia["boton"], 468, 322, 160, 28, "empezar_diseno", color=config.ROJO,
                         principal=True))
    return botones


def tecla(ui, evento):
    """Flechas izquierda / derecha cambian de página."""
    if evento.key == pygame.K_LEFT:
        return ("pagina_didactica", -1)
    if evento.key == pygame.K_RIGHT:
        return ("pagina_didactica", 1)
    return None
