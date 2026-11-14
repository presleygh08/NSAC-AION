# componentes.py
# Piezas de la interfaz que se reutilizan en varias pantallas:
#   - funciones para escribir texto en la ventana
#   - la clase Boton (un rectángulo que se puede clicar)
#   - la clase BarraRecurso (una barra que se llena, p. ej. masa usada / masa máxima)

import pygame
from interfaz import config

# Guardamos las fuentes ya creadas para no crearlas en cada cuadro (es lento).
_fuentes = {}


def obtener_fuente(tamano):
    """Devuelve la fuente de pygame del tamaño pedido (la crea la primera vez)."""
    if tamano not in _fuentes:
        # None = la fuente que trae pygame por defecto.
        _fuentes[tamano] = pygame.font.Font(None, tamano)
    return _fuentes[tamano]


def dibujar_texto(ventana, texto, x, y, tamano=config.LETRA_NORMAL,
                  color=config.COLOR_TEXTO, centrado=False):
    """Escribe una línea de texto. Si centrado=True, (x, y) es el centro del texto."""
    fuente = obtener_fuente(tamano)
    imagen = fuente.render(texto, True, color)   # True = bordes suaves
    rect = imagen.get_rect()
    if centrado:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    ventana.blit(imagen, rect)   # blit = "pegar" la imagen en la ventana


def dibujar_texto_multilinea(ventana, texto, x, y, ancho_max,
                             tamano=config.LETRA_NORMAL, color=config.COLOR_TEXTO):
    """Escribe un texto largo partiéndolo en varias líneas para que no pase de ancho_max.
    Devuelve la coordenada y donde terminó, para saber dónde seguir dibujando."""
    fuente = obtener_fuente(tamano)
    palabras = texto.split(" ")
    linea = ""
    for palabra in palabras:
        prueba = linea + palabra + " "
        # Si la línea con la palabra nueva es muy ancha, escribimos la anterior.
        if fuente.size(prueba)[0] > ancho_max and linea != "":
            dibujar_texto(ventana, linea, x, y, tamano, color)
            y = y + fuente.get_linesize()
            linea = palabra + " "
        else:
            linea = prueba
    if linea != "":
        dibujar_texto(ventana, linea, x, y, tamano, color)
        y = y + fuente.get_linesize()
    return y


class Boton:
    """Un botón rectangular con texto.

    accion: palabra que dice qué hacer al clicarlo (por ejemplo "siguiente").
    valor:  dato extra para la acción (por ejemplo el nombre del destino elegido).
    activo: si es False, el botón se ve gris y no responde.
    seleccionado: si es True, se pinta de otro color (opción elegida).
    subtexto: segunda línea opcional, más pequeña.
    """

    def __init__(self, texto, x, y, ancho, alto, accion, valor=None,
                 activo=True, seleccionado=False, subtexto=""):
        self.texto = texto
        self.rect = pygame.Rect(x, y, ancho, alto)
        self.accion = accion
        self.valor = valor
        self.activo = activo
        self.seleccionado = seleccionado
        self.subtexto = subtexto

    def dibujar(self, ventana):
        # 1. Elegimos el color según el estado del botón.
        pos_mouse = pygame.mouse.get_pos()
        if not self.activo:
            color = config.COLOR_BOTON_INACTIVO
        elif self.seleccionado:
            color = config.COLOR_BOTON_ELEGIDO
        elif self.rect.collidepoint(pos_mouse):   # ¿el mouse está encima?
            color = config.COLOR_BOTON_HOVER
        else:
            color = config.COLOR_BOTON

        # 2. Dibujamos el rectángulo con esquinas redondeadas y un borde.
        pygame.draw.rect(ventana, color, self.rect, border_radius=8)
        pygame.draw.rect(ventana, config.COLOR_BORDE, self.rect, width=1, border_radius=8)

        # 3. Escribimos el texto (y el subtexto si hay).
        color_letra = config.COLOR_TEXTO if self.activo else config.COLOR_TEXTO_SUAVE
        if self.subtexto == "":
            dibujar_texto(ventana, self.texto, self.rect.centerx, self.rect.centery,
                          config.LETRA_NORMAL, color_letra, centrado=True)
        else:
            dibujar_texto(ventana, self.texto, self.rect.x + 15, self.rect.y + 10,
                          config.LETRA_NORMAL, color_letra)
            dibujar_texto(ventana, self.subtexto, self.rect.x + 15, self.rect.y + 38,
                          config.LETRA_PEQUENA, config.COLOR_TEXTO_SUAVE)

    def fue_clicado(self, posicion):
        """True si el botón está activo y la posición (x, y) del clic cae dentro de él."""
        return self.activo and self.rect.collidepoint(posicion)


class BarraRecurso:
    """Barra horizontal que muestra cuánto de un recurso se usa respecto al máximo.
    Verde = hay margen, amarillo = casi al límite (más del 80 %), rojo = se pasó."""

    def __init__(self, nombre, unidad, x, y, ancho=290, alto=18):
        self.nombre = nombre      # p. ej. "Mass"
        self.unidad = unidad      # p. ej. "kg"
        self.x = x
        self.y = y
        self.ancho = ancho
        self.alto = alto

    def dibujar(self, ventana, valor, maximo, texto_sin_maximo=""):
        """valor: lo que se usa. maximo: el límite (o None si aún no hay límite)."""
        # Texto de arriba, por ejemplo: "Mass: 1000 / 4020 kg"
        if maximo is None:
            etiqueta = self.nombre + ": " + str(round(valor)) + " " + self.unidad
            if texto_sin_maximo != "":
                etiqueta = etiqueta + " (" + texto_sin_maximo + ")"
        else:
            etiqueta = (self.nombre + ": " + str(round(valor)) + " / "
                        + str(round(maximo)) + " " + self.unidad)
        dibujar_texto(ventana, etiqueta, self.x, self.y, config.LETRA_PEQUENA)

        # Fondo gris de la barra.
        y_barra = self.y + 22
        fondo = pygame.Rect(self.x, y_barra, self.ancho, self.alto)
        pygame.draw.rect(ventana, config.COLOR_BARRA_FONDO, fondo, border_radius=4)

        # Si no hay máximo, o es 0, no podemos calcular el porcentaje.
        if maximo is None or maximo <= 0:
            return

        fraccion = valor / maximo          # 0.5 = mitad, 1.0 = lleno, 1.3 = se pasó
        if fraccion > 1:
            color = config.COLOR_BARRA_EXCEDE
        elif fraccion > 0.8:
            color = config.COLOR_BARRA_JUSTO
        else:
            color = config.COLOR_BARRA_OK

        ancho_lleno = int(self.ancho * min(fraccion, 1))   # nunca más ancho que la barra
        lleno = pygame.Rect(self.x, y_barra, ancho_lleno, self.alto)
        pygame.draw.rect(ventana, color, lleno, border_radius=4)
