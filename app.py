# app.py
# Punto de entrada del juego. Ejecutar con:  python3 app.py
#
# Aquí están:
#   1. La lectura de los archivos JSON (textos y datos).
#   2. El diccionario "estado" con todo lo que el jugador ha decidido.
#   3. aplicar_accion(): qué pasa cuando se clica cada botón.
#   4. El bucle principal de Pygame: leer eventos -> dibujar -> mostrar.

import json
import sys

import pygame

from interfaz import config
from interfaz import pantallas


# ---------------------------------------------------------------------------
# 1. Lectura de archivos
# ---------------------------------------------------------------------------

def cargar_json(ruta):
    """Lee un archivo JSON y devuelve su contenido (lista o diccionario).
    encoding="utf-8" es necesario porque los nombres tienen tildes (órbita)."""
    with open(ruta, encoding="utf-8") as archivo:
        return json.load(archivo)


def cargar_datos():
    """Lee todos los JSON que usa la interfaz y los junta en un diccionario."""
    return {
        "textos": cargar_json(config.RUTA_TEXTOS),
        "lanzadores": cargar_json(config.RUTA_LANZADORES),
        "destinos": cargar_json(config.RUTA_DESTINOS),
        "mensajes": cargar_json(config.RUTA_MENSAJES),
    }


# ---------------------------------------------------------------------------
# 2. Estado del juego
# ---------------------------------------------------------------------------

def crear_estado_inicial():
    """Devuelve el diccionario con el estado de una partida nueva."""
    return {
        "pantalla": "inicio",        # qué pantalla se está viendo
        "destino": None,             # nombre del destino, como en destinos.json
        "lanzador": None,            # nombre del lanzador, como en lanzadores.json
        # Decisiones de diseño de la nave:
        "masa_seca_kg": 1000,        # kg
        "area_paneles_m2": 10,       # m²
        "isp_s": 320,                # s
        "presupuesto_musd": 500,     # millones de USD (PRUEBA)
        # PRUEBA: estos tres números los calcularán fisica.py / juego.py.
        "potencia_generada_w": 800,  # W
        "potencia_consumo_w": 450,   # W
        "costo_musd": 250,           # millones de USD
        "resultado": None,           # se llena al pulsar "Launch mission"
    }


def evaluar_mision_prueba(estado, datos):
    """PRUEBA. Devuelve un resultado inventado con la misma forma que esperamos
    de juego.py. REEMPLAZAR por juego.evaluar_mision(...) cuando exista.

    Devuelve un diccionario:
      clave:         una de las claves de datos/mensajes.json
      puntaje:       número
      datos_mensaje: valores para llenar los huecos {...} del mensaje
    """
    textos = datos["textos"]
    return {
        "clave": "exito",
        "puntaje": 750,
        "datos_mensaje": {
            "destino": pantallas.nombre_destino(textos, estado["destino"]),
            "lanzador": estado["lanzador"],
            "dv_requerido_m_s": 0,
            "dv_disponible_m_s": 0,
            "consumo_w": estado["potencia_consumo_w"],
            "generada_w": estado["potencia_generada_w"],
            "m0_kg": estado["masa_seca_kg"],
            "capacidad_kg": 0,
            "costo_musd": estado["costo_musd"],
            "presupuesto_musd": estado["presupuesto_musd"],
        },
    }


# ---------------------------------------------------------------------------
# 3. Qué hace cada botón
# ---------------------------------------------------------------------------

def aplicar_accion(estado, accion, valor, datos):
    """Cambia el estado según el botón clicado. Devuelve el estado (nuevo o el mismo)."""
    orden = config.ORDEN_PANTALLAS
    posicion = orden.index(estado["pantalla"])   # 0 = inicio, 1 = objetivo, ...

    if accion == "siguiente" and posicion < len(orden) - 1:
        estado["pantalla"] = orden[posicion + 1]

    elif accion == "atras" and posicion > 0:
        estado["pantalla"] = orden[posicion - 1]

    elif accion == "elegir_destino":
        if estado["destino"] != valor:
            estado["destino"] = valor
            # Al cambiar de destino cambia la capacidad de los lanzadores,
            # así que el jugador debe volver a elegir lanzador.
            estado["lanzador"] = None

    elif accion == "elegir_lanzador":
        estado["lanzador"] = valor

    elif accion == "cambiar":
        # valor es una pareja (clave, paso), por ejemplo ("masa_seca_kg", 100).
        clave, paso = valor
        minimo, maximo, _ = config.LIMITES_DISENO[clave]
        nuevo = estado[clave] + paso
        # No dejamos que el valor salga de los límites.
        if nuevo < minimo:
            nuevo = minimo
        if nuevo > maximo:
            nuevo = maximo
        estado[clave] = nuevo

    elif accion == "simular":
        estado["resultado"] = evaluar_mision_prueba(estado, datos)
        estado["pantalla"] = "resultados"

    elif accion == "redisenar":
        estado["pantalla"] = "diseno"

    elif accion == "menu":
        estado = crear_estado_inicial()   # partida nueva desde cero

    return estado


# ---------------------------------------------------------------------------
# 4. Bucle principal
# ---------------------------------------------------------------------------

def main():
    pygame.init()
    datos = cargar_datos()
    ventana = pygame.display.set_mode((config.ANCHO, config.ALTO))
    pygame.display.set_caption(datos["textos"]["titulo_ventana"])
    reloj = pygame.time.Clock()

    estado = crear_estado_inicial()
    botones = []          # botones de la pantalla actual (los da pantallas.py)
    jugando = True

    while jugando:
        # a) Leer lo que hizo el jugador (teclado, mouse, cerrar ventana).
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                jugando = False
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                # button == 1 es el clic izquierdo.
                for boton in botones:
                    if boton.fue_clicado(evento.pos):
                        estado = aplicar_accion(estado, boton.accion, boton.valor, datos)
                        break   # solo un botón por clic

        # b) Dibujar la pantalla actual (primero borramos todo con el fondo).
        ventana.fill(config.COLOR_FONDO)
        botones = pantallas.dibujar_pantalla(ventana, estado, datos)
        for boton in botones:
            boton.dibujar(ventana)

        # c) Mostrar lo dibujado y esperar para ir a FPS cuadros por segundo.
        pygame.display.flip()
        reloj.tick(config.FPS)

    pygame.quit()
    sys.exit()


# Esto hace que main() solo se ejecute al correr "python3 app.py",
# y no cuando otro archivo hace "import app".
if __name__ == "__main__":
    main()
