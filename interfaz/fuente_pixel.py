# fuente_pixel.py
# Fuente pixel propia del juego (estilo 16 bits), dibujada en código: no necesita
# archivos ni licencias. Cada letra es una cuadrícula de 5 columnas x 7 filas
# ("#" = píxel encendido, "." = apagado). Algunas letras (g, j, p, q, y) tienen
# una 8.ª fila para la parte que baja de la línea.
#
# Cada letra ocupa una "celda" de 5 x 9:
#   fila 0      -> espacio para la tilde de las MAYÚSCULAS (Á, É, Ñ...)
#   filas 1 a 7 -> la letra
#   fila 8      -> la parte que baja (g, p, y...)
# Entre letras se deja 1 columna libre.
#
# La clase FuentePixel tiene los mismos métodos que usa el juego de pygame.font.Font
# (render, size, get_linesize), así el resto del código no cambia.

import pygame

ANCHO_LETRA = 5
ALTO_CELDA = 9
SEPARACION = 1      # columna libre entre letras
INTERLINEA = 1      # fila libre entre líneas

# --- Las letras (texto separado por espacios: una palabra por fila) ---
_DIBUJOS = {
    " ": ". . . . . . .",
    "!": "..#.. ..#.. ..#.. ..#.. ..... ..... ..#..",
    '"': ".#.#. .#.#. ..... ..... ..... ..... .....",
    "#": ".#.#. .#.#. ##### .#.#. ##### .#.#. .#.#.",
    "$": "..#.. .#### #.#.. .###. ..#.# ####. ..#..",
    "%": "##... ##..# ...#. ..#.. .#... #..## ...##",
    "&": ".##.. #..#. #.#.. .#... #.#.# #..#. .##.#",
    "'": "..#.. ..#.. ..... ..... ..... ..... .....",
    "(": "...#. ..#.. .#... .#... .#... ..#.. ...#.",
    ")": ".#... ..#.. ...#. ...#. ...#. ..#.. .#...",
    "*": "..... ..#.. #.#.# .###. #.#.# ..#.. .....",
    "+": "..... ..#.. ..#.. ##### ..#.. ..#.. .....",
    ",": "..... ..... ..... ..... .##.. ..#.. .#...",
    "-": "..... ..... ..... .###. ..... ..... .....",
    ".": "..... ..... ..... ..... ..... .##.. .##..",
    "/": "..... ....# ...#. ..#.. .#... #.... .....",
    "0": ".###. #...# #..## #.#.# ##..# #...# .###.",
    "1": "..#.. .##.. ..#.. ..#.. ..#.. ..#.. .###.",
    "2": ".###. #...# ....# ...#. ..#.. .#... #####",
    "3": "##### ...#. ..#.. ...#. ....# #...# .###.",
    "4": "...#. ..##. .#.#. #..#. ##### ...#. ...#.",
    "5": "##### #.... ####. ....# ....# #...# .###.",
    "6": "..##. .#... #.... ####. #...# #...# .###.",
    "7": "##### ....# ...#. ..#.. .#... .#... .#...",
    "8": ".###. #...# #...# .###. #...# #...# .###.",
    "9": ".###. #...# #...# .#### ....# ...#. .##..",
    ":": "..... .##.. .##.. ..... .##.. .##.. .....",
    ";": "..... .##.. .##.. ..... .##.. ..#.. .#...",
    "<": "...#. ..#.. .#... #.... .#... ..#.. ...#.",
    "=": "..... ..... ##### ..... ##### ..... .....",
    ">": ".#... ..#.. ...#. ....# ...#. ..#.. .#...",
    "?": ".###. #...# ....# ...#. ..#.. ..... ..#..",
    "@": ".###. #...# ....# .##.# #.#.# #.#.# .###.",
    "A": ".###. #...# #...# ##### #...# #...# #...#",
    "B": "####. #...# #...# ####. #...# #...# ####.",
    "C": ".###. #...# #.... #.... #.... #...# .###.",
    "D": "###.. #..#. #...# #...# #...# #..#. ###..",
    "E": "##### #.... #.... ####. #.... #.... #####",
    "F": "##### #.... #.... ####. #.... #.... #....",
    "G": ".###. #...# #.... #.### #...# #...# .####",
    "H": "#...# #...# #...# ##### #...# #...# #...#",
    "I": ".###. ..#.. ..#.. ..#.. ..#.. ..#.. .###.",
    "J": "..### ...#. ...#. ...#. ...#. #..#. .##..",
    "K": "#...# #..#. #.#.. ##... #.#.. #..#. #...#",
    "L": "#.... #.... #.... #.... #.... #.... #####",
    "M": "#...# ##.## #.#.# #.#.# #...# #...# #...#",
    "N": "#...# #...# ##..# #.#.# #..## #...# #...#",
    "O": ".###. #...# #...# #...# #...# #...# .###.",
    "P": "####. #...# #...# ####. #.... #.... #....",
    "Q": ".###. #...# #...# #...# #.#.# #..#. .##.#",
    "R": "####. #...# #...# ####. #.#.. #..#. #...#",
    "S": ".#### #.... #.... .###. ....# ....# ####.",
    "T": "##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..",
    "U": "#...# #...# #...# #...# #...# #...# .###.",
    "V": "#...# #...# #...# #...# #...# .#.#. ..#..",
    "W": "#...# #...# #...# #.#.# #.#.# #.#.# .#.#.",
    "X": "#...# #...# .#.#. ..#.. .#.#. #...# #...#",
    "Y": "#...# #...# #...# .#.#. ..#.. ..#.. ..#..",
    "Z": "##### ....# ...#. ..#.. .#... #.... #####",
    "[": ".###. .#... .#... .#... .#... .#... .###.",
    "\\": "..... #.... .#... ..#.. ...#. ....# .....",
    "]": ".###. ...#. ...#. ...#. ...#. ...#. .###.",
    "^": "..#.. .#.#. #...# ..... ..... ..... .....",
    "_": "..... ..... ..... ..... ..... ..... #####",
    "`": ".#... ..#.. ..... ..... ..... ..... .....",
    "a": "..... ..... .###. ....# .#### #...# .####",
    "b": "#.... #.... #.##. ##..# #...# #...# ####.",
    "c": "..... ..... .###. #.... #.... #...# .###.",
    "d": "....# ....# .##.# #..## #...# #...# .####",
    "e": "..... ..... .###. #...# ##### #.... .###.",
    "f": "..##. .#..# .#... ###.. .#... .#... .#...",
    "g": "..... ..... .#### #...# #...# .#### ....# .###.",
    "h": "#.... #.... #.##. ##..# #...# #...# #...#",
    "i": "..#.. ..... .##.. ..#.. ..#.. ..#.. .###.",
    "j": "...#. ..... ..##. ...#. ...#. ...#. #..#. .##..",
    "k": "#.... #.... #..#. #.#.. ##... #.#.. #..#.",
    "l": ".##.. ..#.. ..#.. ..#.. ..#.. ..#.. .###.",
    "m": "..... ..... ##.#. #.#.# #.#.# #...# #...#",
    "n": "..... ..... #.##. ##..# #...# #...# #...#",
    "o": "..... ..... .###. #...# #...# #...# .###.",
    "p": "..... ..... ####. #...# #...# ####. #.... #....",
    "q": "..... ..... .#### #...# #...# .#### ....# ....#",
    "r": "..... ..... #.##. ##..# #.... #.... #....",
    "s": "..... ..... .###. #.... .###. ....# ####.",
    "t": ".#... .#... ###.. .#... .#... .#..# ..##.",
    "u": "..... ..... #...# #...# #...# #..## .##.#",
    "v": "..... ..... #...# #...# #...# .#.#. ..#..",
    "w": "..... ..... #...# #...# #.#.# #.#.# .#.#.",
    "x": "..... ..... #...# .#.#. ..#.. .#.#. #...#",
    "y": "..... ..... #...# #...# #...# .#### ....# .###.",
    "z": "..... ..... ##### ...#. ..#.. .#... #####",
    "{": "...#. ..#.. ..#.. .#... ..#.. ..#.. ...#.",
    "|": "..#.. ..#.. ..#.. ..#.. ..#.. ..#.. ..#..",
    "}": ".#... ..#.. ..#.. ...#. ..#.. ..#.. .#...",
    "~": "..... ..... .#... #.#.# ...#. ..... .....",
    "°": ".##.. #..#. .##.. ..... ..... ..... .....",
    "²": ".##.. ...#. ..#.. .###. ..... ..... .....",   # v3: para "W/m²"
    "¿": "..#.. ..... ..#.. .#... #.... #...# .###.",
    "¡": "..#.. ..... ..#.. ..#.. ..#.. ..#.. ..#..",
    "ı": "..... ..... .##.. ..#.. ..#.. ..#.. .###.",   # i sin punto (para la í)
}

# Letras con tilde: (letra base, marca). Las minúsculas llevan la marca en las 2 filas
# de arriba de la letra (ahí están vacías); las mayúsculas, en la fila 0 de la celda.
_MARCAS_MINUSCULA = {
    "agudo": ["...#.", "..#.."],
    "tilde_n": [".##.#", "#..#."],
    "dieresis": [".#.#.", "....."],
}
_MARCAS_MAYUSCULA = {
    "agudo": "..##.",
    "tilde_n": ".####",
    "dieresis": ".#.#.",
}
_COMBINADAS = {
    "á": ("a", "agudo"), "é": ("e", "agudo"), "í": ("ı", "agudo"), "ó": ("o", "agudo"),
    "ú": ("u", "agudo"), "ñ": ("n", "tilde_n"), "ü": ("u", "dieresis"),
    "Á": ("A", "agudo"), "É": ("E", "agudo"), "Í": ("I", "agudo"), "Ó": ("O", "agudo"),
    "Ú": ("U", "agudo"), "Ñ": ("N", "tilde_n"), "Ü": ("U", "dieresis"),
}

# Caracteres que no dibujamos y se reemplazan por uno parecido.
_REEMPLAZOS = {"—": "-", "–": "-", "’": "'", "‘": "'", "“": '"', "”": '"', "…": "...",
               "×": "x", "·": "-", "\t": " "}


def _celda(caracter):
    """Devuelve la letra como lista de 9 filas de 5 caracteres ('#' o '.')."""
    if caracter in _COMBINADAS:
        base, marca = _COMBINADAS[caracter]
        filas = _celda(base)
        if base.islower() or base == "ı":
            filas[1] = _MARCAS_MINUSCULA[marca][0]
            filas[2] = _MARCAS_MINUSCULA[marca][1]
        else:
            filas[0] = _MARCAS_MAYUSCULA[marca]
        return filas
    if caracter not in _DIBUJOS:
        # Carácter desconocido: una cajita vacía (así se nota que falta).
        return [".....", "#####", "#...#", "#...#", "#...#", "#...#", "#...#", "#####", "....."]
    filas = _DIBUJOS[caracter].split(" ")
    if caracter == " ":
        filas = ["....."] * 7
    celda = ["....."] + filas            # fila 0 libre para tildes de mayúsculas
    while len(celda) < ALTO_CELDA:
        celda.append(".....")            # fila 8 libre si la letra no baja
    return celda


class FuentePixel:
    """Fuente pixel de un tamaño: escala 1 = letras de 5x7 píxeles, escala 2 = 10x14..."""

    def __init__(self, escala):
        self.escala = escala
        self._letras = {}     # caché: (caracter, color) -> Surface
        self._textos = {}     # caché: (texto, color) -> Surface

    def _limpiar(self, contenido):
        for viejo, nuevo in _REEMPLAZOS.items():
            contenido = contenido.replace(viejo, nuevo)
        return contenido

    def size(self, contenido):
        """(ancho, alto) en píxeles que ocupará el texto."""
        contenido = self._limpiar(contenido)
        e = self.escala
        if contenido == "":
            return (0, ALTO_CELDA * e)
        ancho = len(contenido) * (ANCHO_LETRA + SEPARACION) * e - SEPARACION * e
        return (ancho, ALTO_CELDA * e)

    def get_linesize(self):
        """Distancia entre una línea y la siguiente."""
        return (ALTO_CELDA + INTERLINEA) * self.escala

    def _letra(self, caracter, color):
        """Imagen de una letra (se dibuja una vez y se guarda)."""
        clave = (caracter, color)
        if clave not in self._letras:
            e = self.escala
            imagen = pygame.Surface((ANCHO_LETRA * e, ALTO_CELDA * e), pygame.SRCALPHA)
            filas = _celda(caracter)
            for y in range(ALTO_CELDA):
                for x in range(ANCHO_LETRA):
                    if filas[y][x] == "#":
                        imagen.fill(color, (x * e, y * e, e, e))
            self._letras[clave] = imagen
        return self._letras[clave]

    def render(self, contenido, antialias=False, color=(255, 255, 255)):
        """Imagen del texto (fondo transparente). 'antialias' se ignora: siempre es pixel."""
        color = tuple(color)
        clave = (contenido, color)
        if clave in self._textos:
            return self._textos[clave]
        limpio = self._limpiar(contenido)
        ancho, alto = self.size(limpio)
        imagen = pygame.Surface((max(1, ancho), alto), pygame.SRCALPHA)
        x = 0
        paso = (ANCHO_LETRA + SEPARACION) * self.escala
        for caracter in limpio:
            if caracter != " ":
                imagen.blit(self._letra(caracter, color), (x, 0))
            x = x + paso
        if len(self._textos) > 3000:      # que la caché no crezca sin fin
            self._textos.clear()
        self._textos[clave] = imagen
        return imagen
