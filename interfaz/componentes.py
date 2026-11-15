# componentes.py
# Piezas de la interfaz que se reutilizan en varias pantallas:
#   - posicion_mouse(): el mouse en coordenadas del juego (640x360)
#   - Boton: un rectángulo que se puede clicar
#   - CajaTexto: una caja donde el jugador escribe (nombre o número)
#   - dibujar_ventana(): ventana modal (cuadro de diálogo) con título
#   - crear_selector(): flechas ◀ ▶ para elegir una opción
#   - dibujar_hud_presupuesto(): "Budget left: $X / $Y"
#   - funciones para dar formato a números y buscar traducciones

import pygame

from interfaz import config, estilo


def posicion_mouse():
    """Posición del mouse en coordenadas del juego. La ventana real es ESCALA veces
    más grande que la superficie de 640x360, así que dividimos."""
    x, y = pygame.mouse.get_pos()
    return (x // config.ESCALA, y // config.ESCALA)


class Boton:
    """Un botón rectangular con texto, estilo pixel.

    accion: palabra que dice qué hacer al clicarlo (por ejemplo "siguiente").
    valor:  dato extra para la acción (por ejemplo el id de la misión).
    activo: si es False, el botón se ve gris y no responde.
    color:  color de fondo (por defecto azul de interacción).
    visible: si es False no se dibuja (zona clicable sobre algo que dibujó la pantalla,
             por ejemplo una fila de la parrilla o un marcador del laboratorio).
    icono:  "izquierda" o "derecha" dibuja un triángulo ◀ ▶ en vez de texto.
    """

    def __init__(self, texto, x, y, ancho, alto, accion, valor=None, activo=True,
                 color=config.COLOR_BOTON, tamano=config.LETRA_NORMAL, visible=True, icono=None):
        self.texto = texto
        self.icono = icono
        self.visible = visible
        self.rect = pygame.Rect(x, y, ancho, alto)
        self.accion = accion
        self.valor = valor
        self.activo = activo
        self.color = color
        self.tamano = tamano

    def dibujar(self, sup):
        if not self.visible:
            return
        # 1. Color según el estado: gris si está inactivo, más claro si el mouse está encima.
        if not self.activo:
            fondo = config.COLOR_BOTON_INACTIVO
        elif self.rect.collidepoint(posicion_mouse()):
            fondo = aclarar(self.color)
        else:
            fondo = self.color
        estilo.panel(sup, self.rect, fondo, config.COLOR_BORDE)

        # 2. Triángulo (si es una flecha) o texto centrado.
        color_letra = config.COLOR_TEXTO if self.activo else config.COLOR_TEXTO_SUAVE
        if self.icono is not None:
            dibujar_flecha(sup, self.rect.centerx, self.rect.centery, self.icono, color_letra)
            return
        # Si el texto no cabe en el botón, usamos la letra pequeña.
        tamano = self.tamano
        if estilo.fuente(tamano).size(self.texto)[0] > self.rect.w - 8:
            tamano = config.LETRA_PEQUENA
        estilo.texto(sup, self.texto, self.rect.centerx, self.rect.centery,
                     tamano, color_letra, centrado=True)

    def fue_clicado(self, posicion):
        """True si el botón está activo y la posición (x, y) del clic cae dentro de él."""
        return self.activo and self.rect.collidepoint(posicion)


def dibujar_flecha(sup, cx, cy, direccion, color):
    """Triángulo pixel de 5x7 px: ◀ si direccion == "izquierda", ▶ si "derecha"."""
    for i in range(4):                          # 4 columnas que crecen: 1, 3, 5, 7 px
        alto = 1 + 2 * i
        if direccion == "derecha":
            x = cx + 1 - i       # la columna más alta queda a la izquierda: ▶
        else:
            x = cx - 2 + i       # la columna más alta queda a la derecha: ◀
        pygame.draw.rect(sup, color, (x, cy - alto // 2, 1, alto))


def aclarar(color):
    """Versión un poco más clara de un color (para cuando el mouse está encima)."""
    r, g, b = color
    return (min(255, r + 40), min(255, g + 40), min(255, b + 40))


class CajaTexto:
    """Caja donde el jugador escribe.

    solo_numeros=True: acepta solo dígitos y un punto decimal (cantidades de recursos).
    solo_numeros=False: acepta letras, números y espacio (el nombre del jugador).
    """

    def __init__(self, x, y, ancho, alto, maximo=12, solo_numeros=False, texto=""):
        self.rect = pygame.Rect(x, y, ancho, alto)
        self.maximo = maximo
        self.solo_numeros = solo_numeros
        self.texto = texto

    def escribir(self, evento):
        """Procesa una tecla (evento KEYDOWN). Devuelve True si se pulsó Enter."""
        if evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return True
        if evento.key == pygame.K_BACKSPACE:
            self.texto = self.texto[:-1]        # quita la última letra
            return False
        letra = evento.unicode
        if letra == "" or len(self.texto) >= self.maximo:
            return False
        if self.solo_numeros:
            if letra.isdigit() or (letra == "." and "." not in self.texto):
                self.texto = self.texto + letra
        else:
            if letra.isalnum() or letra == " ":
                self.texto = self.texto + letra
        return False

    def dibujar(self, sup, tiempo):
        estilo.panel(sup, self.rect, config.NEGRO, config.CIAN)
        # Centramos el texto en alto dentro de la caja.
        alto_letra = estilo.fuente(config.LETRA_NORMAL).size("A")[1]
        y_texto = self.rect.y + (self.rect.h - alto_letra) // 2
        rect_texto = estilo.texto(sup, self.texto, self.rect.x + 6, y_texto)
        # Cursor parpadeante: visible medio segundo, oculto medio segundo.
        if int(tiempo * 2) % 2 == 0:
            x_cursor = rect_texto.right + 2 if self.texto else self.rect.x + 6
            pygame.draw.rect(sup, config.CIAN, (x_cursor, self.rect.y + 4, 2, self.rect.h - 8))


def dibujar_ventana(sup, rect, titulo, color_titulo=config.CIAN):
    """Ventana modal: oscurece todo lo de atrás y dibuja un panel con su título.
    Devuelve la y donde puede empezar el contenido."""
    # Capa semitransparente para oscurecer el fondo.
    capa = pygame.Surface((config.ANCHO, config.ALTO))
    capa.set_alpha(150)
    capa.fill(config.NEGRO)
    sup.blit(capa, (0, 0))

    r = pygame.Rect(rect)
    estilo.panel(sup, r, config.COLOR_PANEL, config.COLOR_BORDE)
    estilo.texto(sup, titulo, r.x + 10, r.y + 6, config.LETRA_NORMAL, color_titulo)
    pygame.draw.line(sup, config.COLOR_BORDE, (r.x + 6, r.y + 28), (r.right - 7, r.y + 28))
    return r.y + 36


def crear_selector(botones, x, y, ancho, categoria):
    """Agrega dos botones ◀ y ▶ (triángulos) en una fila. Al clicarlos, app.py recibe la acción
    "selector" con valor (categoria, -1) o (categoria, +1)."""
    botones.append(Boton("", x, y, 18, 18, "selector", (categoria, -1), icono="izquierda"))
    botones.append(Boton("", x + ancho - 18, y, 18, 18, "selector", (categoria, 1), icono="derecha"))


def crear_muestras(sup, botones, x, y, colores, elegido, categoria):
    """Fila de cuadraditos de color clicables (tonos de piel, pelo...), sin nombres.
    El elegido lleva borde amarillo. Al clicar: acción "elegir_opcion" con (categoria, indice)."""
    lado = 14
    for i in range(len(colores)):
        rect = pygame.Rect(x + i * (lado + 4), y, lado, lado)
        borde = config.AMARILLO if i == elegido else config.NEGRO
        pygame.draw.rect(sup, borde, rect.inflate(4, 4))
        pygame.draw.rect(sup, colores[i], rect)
        botones.append(Boton("", rect.x - 2, rect.y - 2, lado + 4, lado + 4, "elegir_opcion",
                             (categoria, i), visible=False))
    return x + len(colores) * (lado + 4)


def dibujar_hud_presupuesto(sup, textos, restante, total, x, y):
    """Texto 'Budget left: $X.XM / $Y.YM', en rojo si es negativo."""
    color = config.COLOR_ERROR if restante < 0 else config.COLOR_OK
    contenido = (textos["laboratorio"]["presupuesto_restante"] + ": "
                 + formatear_musd(restante) + " / " + formatear_musd(total))
    estilo.texto(sup, contenido, x, y, config.LETRA_PEQUENA, color)


# ---------------------------------------------------------------------------
# Funciones para MOSTRAR números y nombres (solo formato, no cálculos del juego)
# ---------------------------------------------------------------------------

def formatear_numero(x):
    """Número corto para la pantalla: 297.37 -> '297', 8.5 -> '8.5', 6.0 -> '6'."""
    if abs(x) >= 100:
        return str(round(x))
    contenido = "%.1f" % x            # un decimal, por ejemplo "8.5" o "6.0"
    if contenido.endswith(".0"):
        contenido = contenido[:-2]    # quitamos el ".0" del final
    return contenido


def formatear_musd(x, decimales=2):
    """Millones de USD como en la especificación: 14.5 -> '$14.5M', -1.5 -> '-$1.5M'."""
    contenido = ("%." + str(decimales) + "f") % abs(x)     # "14.50"
    if "." in contenido:
        contenido = contenido.rstrip("0").rstrip(".")      # "14.50" -> "14.5"
    if x < 0 and contenido != "0":
        return "-$" + contenido + "M"
    return "$" + contenido + "M"


def traducir(diccionario, clave):
    """Busca la clave en una sección de textos_en.json. Si no está, devuelve la
    clave tal cual (así el juego no se rompe si falta una traducción)."""
    return diccionario.get(clave, clave)


def texto_valor(textos, valor, unidad):
    """Valor con su unidad en inglés, por ejemplo '297 m/s' o '20 days'."""
    return formatear_numero(valor) + " " + traducir(textos["unidades"], unidad)


def nombre_recurso(textos, clave):
    """Nombre del recurso en inglés, p. ej. 'Propulsion (delta-v)'."""
    return traducir(textos["recursos"], clave)


def nombre_destino(textos, destino):
    """Destino en inglés, p. ej. 'órbita de Marte' -> 'Mars orbit'."""
    return traducir(textos["destinos"], destino)
