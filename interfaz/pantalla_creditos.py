# pantalla_creditos.py
# Créditos finales (v2, punto 13). Aparece al completar Insane (antes de volver a la
# parrilla) y desde el botón CREDITS del inicio. Los textos salen de
# interfaz/guia_misiones_en.json -> "creditos_finales" (título, frase, equipo e IA).
# Los textos suben desde abajo al entrar; CONTINUE (o Enter) vuelve a la pantalla anterior.

import pygame

from interfaz import config, estilo, sprites
from interfaz.componentes import Boton

ANCHO_TEXTO = 460
SUBIDA = 1.2           # segundos que tardan los textos en llegar a su lugar


def dibujar(sup, ui, textos):
    c = textos["guia"]["creditos_finales"]
    estilo.fondo_estrellas(sup, ui["tiempo"])
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

    return [Boton(textos["botones"]["continuar"], centro - 60, 322, 120, config.ALTO_BOTON,
                  "salir_creditos", color=config.VERDE, principal=True)]
