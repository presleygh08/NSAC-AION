# pantalla_creditos.py
# Créditos finales (v2, punto 13). Aparece al completar Insane (antes de volver a la
# parrilla) y desde el botón Credits del inicio. Los textos salen de
# interfaz/guia_misiones_<idioma>.json -> "creditos_finales" (título, frase, equipo e IA).
#
# v3 (G): botón Sources / Fuentes -> páginas con la nota de estimaciones
# (creditos_finales.estimaciones) y la lista de fuentes ("fuentes" + "fuentes_etiquetas").
# Las páginas se arman solas según cuánto texto cabe en el panel, así ningún texto se sale.
#
# ui["creditos_pagina"]: 0 = créditos; 1, 2, ... = páginas de fuentes.
# Los textos de la página 0 suben desde abajo al entrar; Continue (o Enter) vuelve a la
# pantalla anterior.

import pygame

from interfaz import config, estilo, sprites
from interfaz.componentes import Boton

ANCHO_TEXTO = 460
SUBIDA = 1.2           # segundos que tardan los textos en llegar a su lugar

# Panel de las páginas de fuentes
PANEL_FUENTES = pygame.Rect(16, 40, 608, 272)
MARGEN_PANEL = 10
SEPARACION = 6         # espacio entre una fuente y la siguiente


def alto_bloque(bloque, ancho):
    """Alto en píxeles de un bloque (lista de (texto, color)) escrito con letra pequeña."""
    alto_linea = estilo.fuente(config.LETRA_PEQUENA).get_linesize()
    lineas = 0
    for contenido, _ in bloque:
        lineas = lineas + len(estilo.partir_lineas(contenido, ancho, config.LETRA_PEQUENA))
    return lineas * alto_linea


def bloques_fuentes(textos):
    """Lista de bloques: primero la nota de estimaciones y luego una fuente por bloque
    (nombre legible en cian + dirección en gris)."""
    guia = textos["guia"]
    t = textos["creditos"]
    bloques = [[(t["estimaciones_titulo"], config.AMARILLO),
                (guia["creditos_finales"]["estimaciones"], config.COLOR_TEXTO)]]
    etiquetas = guia.get("fuentes_etiquetas", {})
    for clave, direccion in guia.get("fuentes", {}).items():
        bloques.append([(etiquetas.get(clave, clave), config.CIAN),
                        (direccion, config.COLOR_TEXTO_SUAVE)])
    return bloques


def paginas_fuentes(textos):
    """Reparte los bloques en páginas que caben en PANEL_FUENTES."""
    ancho = PANEL_FUENTES.w - 2 * MARGEN_PANEL
    alto_max = PANEL_FUENTES.h - 2 * MARGEN_PANEL
    paginas = []
    pagina = []
    alto = 0
    for bloque in bloques_fuentes(textos):
        h = alto_bloque(bloque, ancho)
        if pagina and alto + h > alto_max:
            paginas.append(pagina)
            pagina = []
            alto = 0
        pagina.append(bloque)
        alto = alto + h + SEPARACION
    if pagina:
        paginas.append(pagina)
    return paginas


def dibujar_portada(sup, ui, textos):
    """Página 0: título, AION celebrando, frase, equipo e IA (suben desde abajo)."""
    c = textos["guia"]["creditos_finales"]
    segundos = ui["tiempo"] - ui.get("creditos_t0", ui["tiempo"])
    f = min(1.0, segundos / SUBIDA)
    desplazamiento = int((1 - f) ** 2 * 120)          # empieza 120 px más abajo y frena
    centro = config.ANCHO // 2
    x = centro - ANCHO_TEXTO // 2

    y = 34 + desplazamiento
    estilo.texto_contorno(sup, c["titulo"], centro, y, config.LETRA_TITULO, config.AMARILLO, config.NEGRO, 2)
    # AION celebrando, al doble de tamaño
    retrato = pygame.Surface((32, 32))
    sprites.dibujar_aion(retrato, 0, 0, "celebrando", ui["tiempo"])
    sup.blit(pygame.transform.scale(retrato, (64, 64)), (centro - 32, y + 22))

    y = y + 96
    y = estilo.texto_multilinea(sup, c["frase"], x, y, ANCHO_TEXTO, config.LETRA_PEQUENA) + 12
    y = estilo.texto_multilinea(sup, c["equipo"], x, y, ANCHO_TEXTO, config.LETRA_PEQUENA, config.CIAN) + 12
    estilo.texto_multilinea(sup, c["ia"], x, y, ANCHO_TEXTO, config.LETRA_PEQUENA, config.COLOR_TEXTO_SUAVE)


def dibujar_pagina_fuentes(sup, textos, pagina, numero, total):
    """Una página de fuentes dentro de su panel."""
    t = textos["creditos"]
    centro = config.ANCHO // 2
    estilo.texto_contorno(sup, t["fuentes_titulo"], centro, 20, config.LETRA_NORMAL, config.AMARILLO,
                          config.NEGRO, 1)
    estilo.panel(sup, PANEL_FUENTES)
    x = PANEL_FUENTES.x + MARGEN_PANEL
    y = PANEL_FUENTES.y + MARGEN_PANEL
    ancho = PANEL_FUENTES.w - 2 * MARGEN_PANEL
    for bloque in pagina:
        for contenido, color in bloque:
            y = estilo.texto_multilinea(sup, contenido, x, y, ancho, config.LETRA_PEQUENA, color)
        y = y + SEPARACION
    estilo.texto(sup, t["pagina"].replace("{n}", str(numero)).replace("{total}", str(total)),
                 PANEL_FUENTES.right, 16, config.LETRA_PEQUENA, config.COLOR_TEXTO_SUAVE, derecha=True)


def dibujar(sup, ui, textos):
    estilo.fondo_estrellas(sup, ui["tiempo"])
    b = textos["botones"]
    centro = config.ANCHO // 2
    paginas = paginas_fuentes(textos)
    numero = min(ui.get("creditos_pagina", 0), len(paginas))
    ui["creditos_pagina"] = numero

    if numero == 0:
        dibujar_portada(sup, ui, textos)
        return [Boton(b["continuar"], centro - 60, 322, 120, config.ALTO_BOTON,
                      "salir_creditos", color=config.VERDE, principal=True),
                Boton(b["fuentes"], config.ANCHO - 136, 322, 120, config.ALTO_BOTON,
                      "creditos_pagina", 1)]

    dibujar_pagina_fuentes(sup, textos, paginas[numero - 1], numero, len(paginas))
    botones = [Boton(b["anterior"], 16, 322, 120, config.ALTO_BOTON, "creditos_pagina", numero - 1),
               Boton(b["continuar"], config.ANCHO - 136, 322, 120, config.ALTO_BOTON,
                     "salir_creditos", color=config.VERDE, principal=(numero == len(paginas)))]
    if numero < len(paginas):
        # Enter pasa a la siguiente página de fuentes
        botones.append(Boton(b["siguiente"], centro - 60, 322, 120, config.ALTO_BOTON,
                             "creditos_pagina", numero + 1, principal=True))
    return botones
