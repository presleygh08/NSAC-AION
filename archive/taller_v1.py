# taller.py
# Taller de reparto (CML 3) y revisión del presupuesto (CML 4).
# Versión simple con botones - y +. Más adelante la reemplaza el laboratorio
# de docs/especificacion-interfaz.md (sección 4).
#
# Regla del contrato: aquí NUNCA se lee estado["recursos"] (trae los mínimos
# y óptimos ocultos). Solo se usa nucleo.recursos_visibles(estado).

import pygame

import nucleo
from interfaz import config
from interfaz.componentes import (Boton, dibujar_texto, dibujar_texto_multilinea,
                                  formatear_musd, texto_valor, traducir)

Y_PRIMER_PANEL = 205
ALTO_PANEL = 62
SEPARACION = 70          # cabe hasta 6 recursos (Insane) antes de los botones de abajo


# ---------------------------------------------------------------------------
# Taller
# ---------------------------------------------------------------------------

def dibujar_barra_presupuesto(ventana, textos, estado):
    """Barra con el presupuesto que queda. Se pone roja si es negativo."""
    restante = nucleo.presupuesto_restante(estado)
    total = estado["presupuesto_musd"]

    if restante < 0:
        color = config.COLOR_BARRA_EXCEDE
    else:
        color = config.COLOR_BARRA_OK

    etiqueta = (textos["taller"]["presupuesto_restante"] + ": "
                + formatear_musd(restante) + " / " + formatear_musd(total))
    dibujar_texto(ventana, etiqueta, config.MARGEN, 130, config.LETRA_NORMAL, color)

    # Fondo gris de la barra y parte llena (lo que queda sin gastar).
    ancho_barra = config.ANCHO - 2 * config.MARGEN
    fondo = pygame.Rect(config.MARGEN, 162, ancho_barra, 20)
    pygame.draw.rect(ventana, config.COLOR_BARRA_FONDO, fondo, border_radius=4)
    if restante < 0:
        # Se pasó: barra roja completa para que se note.
        pygame.draw.rect(ventana, color, fondo, border_radius=4)
    elif total > 0:
        ancho_lleno = int(ancho_barra * restante / total)
        lleno = pygame.Rect(config.MARGEN, 162, ancho_lleno, 20)
        pygame.draw.rect(ventana, color, lleno, border_radius=4)


def dibujar_panel_recurso(ventana, botones, textos, recurso, y):
    """Un panel por recurso: nombre, dinero asignado, lo que compra y botones - y +."""
    t = textos["taller"]
    panel = pygame.Rect(config.MARGEN, y, config.ANCHO - 2 * config.MARGEN, ALTO_PANEL)
    pygame.draw.rect(ventana, config.COLOR_PANEL, panel, border_radius=8)

    nombre = traducir(textos["recursos"], recurso["clave"])
    dibujar_texto(ventana, nombre, config.MARGEN + 15, y + 8)
    dibujar_texto(ventana, t["valor"] + ": "
                  + texto_valor(textos, recurso["valor"], recurso["unidad"]),
                  config.MARGEN + 15, y + 36, config.LETRA_PEQUENA, config.COLOR_TEXTO_SUAVE)

    # Botones - y + con el dinero en el medio. El valor del botón es la clave
    # del recurso: app.py sabe así a qué recurso darle o quitarle dinero.
    x = config.ANCHO - config.MARGEN - 300
    hay_dinero = recurso["dinero_musd"] > 0          # no se puede bajar de 0
    botones.append(Boton("-", x, y + 11, 50, 40, "menos", valor=recurso["clave"],
                         activo=hay_dinero))
    dibujar_texto(ventana, t["dinero"] + ": " + formatear_musd(recurso["dinero_musd"]),
                  x + 125, y + ALTO_PANEL // 2, centrado=True)
    botones.append(Boton("+", x + 200, y + 11, 50, 40, "mas", valor=recurso["clave"]))


def dibujar_taller(ventana, ui, textos):
    t = textos["taller"]
    estado = ui["estado"]
    dibujar_texto(ventana, t["titulo"] + " - " + ui["mision_nombre"],
                  config.MARGEN, 30, config.LETRA_TITULO)
    dibujar_texto_multilinea(ventana, t["ayuda"], config.MARGEN, 85,
                             config.ANCHO - 2 * config.MARGEN,
                             config.LETRA_PEQUENA, config.COLOR_TEXTO_SUAVE)
    dibujar_barra_presupuesto(ventana, textos, estado)

    botones = []
    y = Y_PRIMER_PANEL
    for recurso in nucleo.recursos_visibles(estado):
        dibujar_panel_recurso(ventana, botones, textos, recurso, y)
        y = y + SEPARACION

    botones.append(Boton(textos["botones"]["atras"], config.MARGEN, config.Y_BOTONES_NAV,
                         140, 50, "ir_info"))
    botones.append(Boton(textos["botones"]["revisar"], config.ANCHO - config.MARGEN - 240,
                         config.Y_BOTONES_NAV, 240, 50, "revisar"))
    return botones


# ---------------------------------------------------------------------------
# Revisión (CML 4)
# ---------------------------------------------------------------------------

def dibujar_revision(ventana, ui, textos):
    """Muestra lo que devolvió nucleo.revisar() (guardado en ui["revision"])."""
    t = textos["revision"]
    revision = ui["revision"]
    ancho = config.ANCHO - 2 * config.MARGEN
    dibujar_texto(ventana, t["titulo"], config.MARGEN, 30, config.LETRA_TITULO)

    if revision["ok"]:
        # Dentro del presupuesto. El núcleo ya pasó a la fase de simulación,
        # así que no hay botón para volver al taller.
        dibujar_texto_multilinea(ventana, t["ok"], config.MARGEN, 130, ancho,
                                 config.LETRA_NORMAL, config.COLOR_BARRA_OK)
        dibujar_texto_multilinea(ventana, t["aviso_ok"], config.MARGEN, 180, ancho,
                                 config.LETRA_PEQUENA, config.COLOR_TEXTO_SUAVE)
        boton = Boton(textos["botones"]["lanzar"], config.ANCHO - config.MARGEN - 240,
                      config.Y_BOTONES_NAV, 240, 50, "lanzar")
    else:
        # Se pasó del presupuesto: mostramos el mensaje del núcleo y volvemos al taller.
        dibujar_texto_multilinea(ventana, revision["mensaje"], config.MARGEN, 130, ancho,
                                 config.LETRA_NORMAL, config.COLOR_BARRA_EXCEDE)
        boton = Boton(textos["botones"]["volver_taller"], config.MARGEN,
                      config.Y_BOTONES_NAV, 240, 50, "ir_taller")
    return [boton]
