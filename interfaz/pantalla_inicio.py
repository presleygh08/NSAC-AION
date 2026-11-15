# pantalla_inicio.py
# Pantalla de inicio: título STAR FORGE, la Tierra con un cohete despegando y la caja
# para escribir el nombre del jugador (callsign). Botón CREDITS -> créditos (v2, punto 13).
# Botones EN | ES para elegir el idioma (v3, E); el juego abre en inglés.
#
# Cada pantalla tiene:
#   dibujar(sup, ui, textos) -> lista de botones
#   tecla(ui, evento)        -> (accion, valor) si la tecla dispara una acción, o None

from interfaz import config, estilo, sprites
from interfaz.componentes import Boton


def dibujar(sup, ui, textos):
    t = textos["inicio"]
    estilo.fondo_estrellas(sup, ui["tiempo"])
    sprites.dibujar_tierra_y_cohete(sup, ui["tiempo"])

    centro = config.ANCHO // 2
    # Título grande con contorno oscuro y una "sombra" roja desplazada (estilo arcade).
    estilo.texto_contorno(sup, t["titulo"], centro + 3, 63, config.LETRA_GIGANTE, config.ROJO,
                          config.NEGRO, 2)
    estilo.texto_contorno(sup, t["titulo"], centro, 60, config.LETRA_GIGANTE, config.AMARILLO,
                          config.NEGRO, 2)
    estilo.texto(sup, t["subtitulo"], centro, 100, config.LETRA_NORMAL, config.CIAN, centrado=True)

    estilo.texto(sup, t["pide_nombre"], centro, 150, config.LETRA_NORMAL, centrado=True)
    caja = ui["caja_nombre"]
    caja.dibujar(sup, ui["tiempo"])

    estilo.texto(sup, t["ayuda"], centro, 238, config.LETRA_PEQUENA, config.COLOR_TEXTO_SUAVE,
                 centrado=True)
    botones = [Boton(textos["botones"]["jugar"], centro - 50, 200, 100, config.ALTO_BOTON,
                     "jugar", color=config.VERDE, principal=True),
               Boton(textos["botones"]["creditos"], config.ANCHO - 116, 326, 100, config.ALTO_BOTON,
                     "ver_creditos")]
    # Idioma (v3, E): botones EN | ES abajo a la izquierda; el activo va en verde.
    x = 16
    for idioma in config.IDIOMAS:
        color = config.VERDE if ui["idioma"] == idioma else config.COLOR_BOTON
        botones.append(Boton(textos["idioma"][idioma], x, 326, 40, config.ALTO_BOTON, "idioma",
                             idioma, color=color))
        x = x + 46
    return botones


def tecla(ui, evento):
    """Las letras van a la caja del nombre. Enter = PLAY."""
    if ui["caja_nombre"].escribir(evento):
        return ("jugar", None)
    return None
