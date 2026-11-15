# pantalla_avatar.py
# "Create your avatar" (sección 3.2 de la especificación).
#   Izquierda: el avatar de frente y de cuerpo completo, grande, y debajo la vista
#              "desde arriba" que caminará en el laboratorio (mismos colores).
#   Derecha:   una fila por categoría con flechas ◀ ▶. Los colores (piel, pelo, ojos)
#              se eligen además con cuadraditos clicables, sin nombres.
# El avatar es un diccionario de índices guardado en ui["jugador"]["avatar"].
#
# Inclusión: los cuerpos se llaman Body 1, 2 y 3 (sin etiquetas de género) y
# cualquier ropa, peinado o accesorio sirve con cualquier cuerpo.

from interfaz import config, estilo, sprites
from interfaz.componentes import Boton, crear_muestras, crear_selector

# Orden en que se muestran las categorías.
CATEGORIAS = ["cuerpo", "piel", "pelo", "color_pelo", "ojos", "color_ojos",
              "accesorio", "polo", "pantalon"]

# Categorías que se eligen con muestras de color (sin nombre).
MUESTRAS = {
    "piel": sprites.TONOS_PIEL,
    "color_pelo": sprites.COLORES_PELO,
    "color_ojos": sprites.COLORES_OJOS,
}

X_ETIQUETA = 232
X_SELECTOR = 314
ANCHO_SELECTOR = 306
Y_PRIMERA_FILA = 58
ALTO_FILA = 26


def dibujar_vista_previa(sup, ui, textos):
    """Panel izquierdo: avatar de frente + sprite desde arriba que camina girando."""
    avatar = ui["jugador"]["avatar"]
    estilo.panel(sup, (16, 54, 204, 270))
    sprites.dibujar_avatar(sup, avatar, 30, 68, 6)          # 96 x 192 px

    # Vista desde arriba: cambia de dirección cada segundo y da pasos 4 veces por segundo.
    direccion = sprites.DIRECCIONES[int(ui["tiempo"]) % 4]
    cuadro = int(ui["tiempo"] * 4) % 2
    # Centrado sobre la vista de arriba, pero sin salirse del panel (v3, C: en español es más largo)
    ancho_etiqueta = estilo.fuente(config.LETRA_PEQUENA).size(textos["avatar"]["vista_lab"])[0]
    x_etiqueta = min(172, 214 - ancho_etiqueta // 2)
    estilo.texto(sup, textos["avatar"]["vista_lab"], x_etiqueta, 166, config.LETRA_PEQUENA,
                 config.COLOR_TEXTO_SUAVE, centrado=True)
    estilo.panel(sup, (142, 176, 60, 60), config.GRIS_SUELO, config.GRIS)
    sprites.dibujar_avatar_arriba(sup, avatar, 148, 182, direccion, cuadro, 3)   # 48 x 48 px

    estilo.texto(sup, ui["jugador"]["nombre"], 118, 300, config.LETRA_NORMAL, config.CIAN,
                 centrado=True)


def nombre_opcion(textos, categoria, indice):
    """Nombre en inglés de la opción (las categorías de color no tienen nombre)."""
    return textos["avatar"]["opciones"][categoria][indice]


def dibujar(sup, ui, textos):
    t = textos["avatar"]
    avatar = ui["jugador"]["avatar"]
    estilo.fondo_estrellas(sup, ui["tiempo"])
    estilo.texto(sup, t["titulo"], config.ANCHO // 2, 18, config.LETRA_TITULO, config.AMARILLO,
                 centrado=True)
    estilo.texto(sup, t["ayuda"], config.ANCHO // 2, 42, config.LETRA_PEQUENA,
                 config.COLOR_TEXTO_SUAVE, centrado=True)
    dibujar_vista_previa(sup, ui, textos)

    botones = []
    centro_selector = X_SELECTOR + ANCHO_SELECTOR // 2
    y = Y_PRIMERA_FILA
    for categoria in CATEGORIAS:
        estilo.texto(sup, t["categorias"][categoria], X_ETIQUETA, y + 6, config.LETRA_PEQUENA,
                     config.CIAN)
        crear_selector(botones, X_SELECTOR, y, ANCHO_SELECTOR, categoria)
        if categoria in MUESTRAS:
            colores = MUESTRAS[categoria]
            ancho_muestras = len(colores) * 18
            crear_muestras(sup, botones, centro_selector - ancho_muestras // 2, y + 2, colores,
                           avatar[categoria], categoria)
        else:
            estilo.texto(sup, nombre_opcion(textos, categoria, avatar[categoria]), centro_selector,
                         y + 9, config.LETRA_NORMAL, centrado=True)
        y = y + ALTO_FILA

    botones.append(Boton(textos["botones"]["aleatorio"], X_ETIQUETA, 304, 120, config.ALTO_BOTON,
                         "avatar_aleatorio"))
    botones.append(Boton(textos["botones"]["continuar"], 500, 304, 120, config.ALTO_BOTON,
                         "avatar_listo", color=config.VERDE, principal=True))
    return botones
