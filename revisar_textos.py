# revisar_textos.py
# Modo de prueba (v3, C): recorre TODAS las pantallas y ventanas del juego, en inglés y en
# español, sin abrir ventana, y avisa si algún texto se sale de su cuadro.
#
#   python3.12 revisar_textos.py            -> lista de problemas (o "OK")
#   python3.12 revisar_textos.py --capturas -> además guarda una imagen PNG de cada pantalla
#                                              en la carpeta capturas_textos/ (para mirarlas)
#
# Cómo detecta un problema: mientras se dibuja, estilo.REGISTRO anota cada texto y cada
# cuadro (estilo.panel: ventanas, botones, cajas). Un texto está MAL si:
#   1. se sale de la pantalla de 640x360, o
#   2. toca un cuadro que se dibujó ANTES que él (o sea, que está debajo del texto) pero
#      no queda completo dentro de su interior (el cuadro tiene un marco de 2 px).
# Los cuadros dibujados DESPUÉS del texto lo tapan (por ejemplo una ventana encima de la
# sala), así que esos no cuentan. Tampoco cuenta un cuadro de abajo si el texto está
# entero sobre otro cuadro dibujado encima de ese (una notificación sobre el diálogo).
#   3. se monta sobre OTRO texto distinto (por ejemplo una etiqueta larga sobre su valor),
#      salvo que entre los dos se haya dibujado un cuadro que tape al primero.
#
# Este archivo NO es parte del juego: solo usa las funciones de app.py, nucleo.py e interfaz/.
# Para armar resultados con 5 estrellas sí lee los mínimos y óptimos (la interfaz nunca lo hace).

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")     # sin ventana
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")     # sin sonido

import pygame

import app
import nucleo
from interfaz import config, estilo, laboratorio, notificaciones, simulacion

PANTALLA = pygame.Rect(0, 0, config.ANCHO, config.ALTO)
NOMBRE_LARGO = "WWWWWWWWWWWW"      # 12 letras: el nombre más ancho posible
MARCO = 2                          # px del marco de estilo.panel

GUARDAR = "--capturas" in sys.argv
CARPETA_CAPTURAS = os.path.join(config.RUTA_PROYECTO, "capturas_textos")

problemas = []
cantidad_cuadros = [0]


def tapado(registro, j, i, rect):
    """True si entre el cuadro j y el texto i se dibujó otro cuadro cuyo interior
    contiene todo el texto (entonces el cuadro j queda tapado debajo)."""
    for k in range(j + 1, i):
        tipo_k, cuadro, _ = registro[k]
        if tipo_k == "panel" and cuadro.inflate(-2 * MARCO, -2 * MARCO).contains(rect):
            return True
    return False


def texto_encimado(registro, i):
    """Regla 3: el texto i pisa a un texto anterior distinto que sigue a la vista."""
    _, rect, contenido = registro[i]
    for k in range(i):
        tipo_k, otro, contenido_k = registro[k]
        if tipo_k != "texto" or contenido_k == contenido or otro.w == 0:
            continue
        cruce = rect.clip(otro)
        if cruce.w <= 1 or cruce.h <= 1:
            continue
        tapado_por_cuadro = False
        for j in range(k + 1, i):
            tipo_j, cuadro, _ = registro[j]
            if tipo_j == "panel" and cuadro.contains(cruce):
                tapado_por_cuadro = True
        if not tapado_por_cuadro:
            return "se monta sobre el texto " + repr(contenido_k[:30])
    return None


def revisar_registro(registro, nombre):
    """Aplica las dos reglas a lo que se dibujó en un cuadro. Agrega los problemas."""
    vistos = set()
    for i in range(len(registro)):
        tipo, rect, contenido = registro[i]
        if tipo != "texto" or rect.w == 0:
            continue
        motivo = None
        if not PANTALLA.contains(rect):
            motivo = "sale de la pantalla"
        else:
            for j in range(i):
                tipo_j, cuadro, _ = registro[j]
                if tipo_j != "panel" or not rect.colliderect(cuadro):
                    continue
                if tapado(registro, j, i, rect):
                    continue
                interior = cuadro.inflate(-2 * MARCO, -2 * MARCO)
                if not interior.contains(rect):
                    motivo = "cruza el borde del cuadro " + str(tuple(cuadro))
                    break
        if motivo is None:
            motivo = texto_encimado(registro, i)
        if motivo is not None and (contenido, motivo) not in vistos:
            vistos.add((contenido, motivo))
            problemas.append((nombre, contenido, tuple(rect), motivo))


def dibujar(lienzo, ui, nombre):
    """Dibuja un cuadro completo de la pantalla actual y lo revisa."""
    estilo.REGISTRO = []
    app.dibujar_cuadro(lienzo, ui, app.textos_juego)
    revisar_registro(estilo.REGISTRO, ui["idioma"] + " | " + nombre)
    estilo.REGISTRO = None
    cantidad_cuadros[0] = cantidad_cuadros[0] + 1
    if GUARDAR:
        archivo = (ui["idioma"] + "_" + nombre).replace(" ", "_").replace("/", "-").replace("|", "")
        pygame.image.save(lienzo, os.path.join(CARPETA_CAPTURAS, archivo + ".png"))


# ---------------------------------------------------------------------------
# Repartos de prueba (solo para llegar a cada pantalla)
# ---------------------------------------------------------------------------

def repartir_por_factor(estado, factor_min=None, factor_opt=None):
    """Asigna a cada recurso factor x mínimo o factor x óptimo."""
    for r in estado["recursos"]:
        if factor_opt is not None:
            valor = r["optimo"] * factor_opt
        else:
            valor = r["minimo"] * factor_min
        nucleo.repartir_valor(estado, r["clave"], valor)


def nuevo_lab(ui, mision_id):
    """Misión nueva en el laboratorio, con el nombre más largo posible."""
    app.elegir_mision(ui, mision_id)
    app.empezar_mision(ui)
    ui["pantalla"] = "laboratorio"
    ui["lab"]["t_inicio"] = ui["tiempo"]


# ---------------------------------------------------------------------------
# Recorrido por las pantallas
# ---------------------------------------------------------------------------

def recorrer_menus(lienzo, ui):
    ui["pantalla"] = "inicio"
    ui["caja_nombre"].texto = NOMBRE_LARGO
    dibujar(lienzo, ui, "inicio")

    ui["pantalla"] = "avatar"
    avatar = ui["jugador"]["avatar"]
    for categoria in avatar:                       # cada opción de cada categoría
        for indice in range(app.sprites.CANTIDAD_OPCIONES[categoria]):
            avatar[categoria] = indice
            dibujar(lienzo, ui, "avatar " + categoria + " " + str(indice))
        avatar[categoria] = 0

    ui["pantalla"] = "misiones"
    for fila in nucleo.cargar_misiones(ui["progreso"]):
        ui["mision_vista"] = fila["id"]
        dibujar(lienzo, ui, "misiones " + fila["id"])
    # Con una completada (muestra estrellas y "Best: 100")
    ui["progreso"]["completadas"]["easy_cubesat"] = 100
    ui["progreso"]["estrellas"]["easy_cubesat"] = 5
    dibujar(lienzo, ui, "misiones completada")

    for fila in nucleo.cargar_misiones(ui["progreso"]):
        app.elegir_mision(ui, fila["id"])
        ui["pantalla"] = "info_mision"
        ui["ficha"] = None
        dibujar(lienzo, ui, "info " + fila["id"])
        ui["pantalla"] = "didactica"
        for pagina in range(8):
            ui["pagina_didactica"] = pagina
            dibujar(lienzo, ui, "didactica " + fila["id"] + " p" + str(pagina))
        ui["pausa"] = True
        dibujar(lienzo, ui, "pausa didactica")
        ui["pausa"] = False

    for clave in ("bienvenida", "desbloqueo", "reintento", "depuracion"):
        ui["pantalla"] = "misiones"
        texto = app.textos_juego["notificaciones"][clave].replace("{mision}", "Exoplanet SmallSat to LEO")
        notificaciones.mostrar_notificacion(ui, texto, "feliz", duracion=60)
        notificaciones.actual(ui)                    # empieza a mostrarse ahora...
        ui["tiempo"] = ui["tiempo"] + 1              # ...y 1 s después ya terminó de subir
        dibujar(lienzo, ui, "notificacion " + clave)
        ui["notificaciones"] = []

    app.ir_a_creditos(ui, "inicio")
    ui["creditos_t0"] = ui["tiempo"] - 10            # textos ya en su lugar
    for pagina in range(10):
        ui["creditos_pagina"] = pagina
        dibujar(lienzo, ui, "creditos p" + str(pagina))


def recorrer_laboratorio(lienzo, ui, mision_id):
    nuevo_lab(ui, mision_id)
    lab = ui["lab"]
    estado = ui["estado"]
    for fase in ("cml1", "cml2", "cml3", "cml4"):
        lab["fase"] = fase
        lab["cortinas_t0"] = ui["tiempo"] - 5
        lab["pistas_vistas"] = True
        dibujar(lienzo, ui, mision_id + " lab " + fase)
    for ventana in ("briefing", "pistas", "pistas_guardadas", "archivo"):
        lab["ventana"] = ventana
        dibujar(lienzo, ui, mision_id + " ventana " + ventana)
    for r in nucleo.recursos_visibles(estado):
        laboratorio.abrir_estacion(lab, estado, r["clave"])
        lab["caja"].texto = "1234567.89"
        lab["error"] = True
        dibujar(lienzo, ui, mision_id + " estacion " + r["clave"])
    lab["ventana"] = "aion"
    lab["faq"] = None
    dibujar(lienzo, ui, mision_id + " aion lista")
    for i in range(len(app.textos_juego["guia"]["aion_faq"])):
        lab["faq"] = i
        dibujar(lienzo, ui, mision_id + " aion " + str(i))
    lab["ventana"] = None
    ui["pausa"] = True
    dibujar(lienzo, ui, mision_id + " pausa")
    ui["pausa"] = False
    # Revisión del presupuesto: excedida y aprobada
    repartir_por_factor(estado, factor_opt=3)
    lab["revision"] = nucleo.revisar(estado)
    lab["ventana"] = "revision"
    dibujar(lienzo, ui, mision_id + " revision excedida")
    repartir_por_factor(estado, factor_opt=1)
    lab["revision"] = nucleo.revisar(estado)
    dibujar(lienzo, ui, mision_id + " revision ok")


def jugar_hasta_resultados(lienzo, ui, mision_id, nombre, factor_min=None, factor_opt=None,
                           cuadros_sim=False):
    """Juega la misión con ese reparto, (opcional) revisa la simulación y los resultados."""
    nuevo_lab(ui, mision_id)
    repartir_por_factor(ui["estado"], factor_min, factor_opt)
    # en el laboratorio también se "confirman" las estaciones (TRY AGAIN las conserva)
    for r in nucleo.recursos_visibles(ui["estado"]):
        ui["lab"]["escrito"][r["clave"]] = str(round(r["valor"], 2))
        ui["lab"]["hechas"].append(r["clave"])
        ui["lab"]["partes"][r["clave"]] = ui["tiempo"] - 10
    nucleo.revisar(ui["estado"])
    app.aplicar_accion(ui, "confirmar_lanzamiento", None)
    if cuadros_sim:
        inicio = ui["tiempo"]
        while ui["pantalla"] == "simulacion" and ui["tiempo"] - inicio < 40:
            dibujar(lienzo, ui, mision_id + " sim " + nombre + " t" + str(round(ui["tiempo"] - inicio, 1)))
            ui["tiempo"] = ui["tiempo"] + 0.5
    app.ir_a_resultados(ui)
    ui["resultados_t0"] = ui["tiempo"] - 10
    dibujar(lienzo, ui, mision_id + " resultados " + nombre)
    ui["notificaciones"] = []


def recorrer_idioma(lienzo, idioma):
    ui = app.crear_ui()
    app.cambiar_idioma(ui, idioma)
    ui["jugador"]["nombre"] = NOMBRE_LARGO
    ui["tiempo"] = 100.0
    nucleo.DESBLOQUEO_EN_ORDEN = False
    recorrer_menus(lienzo, ui)
    for fila in nucleo.cargar_misiones(ui["progreso"]):
        mid = fila["id"]
        recorrer_laboratorio(lienzo, ui, mid)
        jugar_hasta_resultados(lienzo, ui, mid, "5 estrellas", factor_opt=1, cuadros_sim=True)
        jugar_hasta_resultados(lienzo, ui, mid, "parcial", factor_min=1.02)
        jugar_hasta_resultados(lienzo, ui, mid, "falla", factor_min=0.5, cuadros_sim=True)
        # TRY AGAIN: el laboratorio continúa en CML 4 (v3, B)
        app.aplicar_accion(ui, "reintentar", None)
        assert ui["lab"]["fase"] == "cml4", ui["lab"]["fase"]
        dibujar(lienzo, ui, mid + " reintento cml4")


def main():
    pygame.init()
    pygame.display.set_mode((config.ANCHO, config.ALTO))
    lienzo = pygame.Surface((config.ANCHO, config.ALTO))
    if GUARDAR:
        os.makedirs(CARPETA_CAPTURAS, exist_ok=True)
    for idioma in config.IDIOMAS:
        recorrer_idioma(lienzo, idioma)
    print("Cuadros revisados:", cantidad_cuadros[0])
    if not problemas:
        print("OK: ningún texto se sale de su cuadro (en", ", ".join(config.IDIOMAS) + ")")
        return 0
    print("Textos fuera de su cuadro:", len(problemas))
    for nombre, contenido, rect, motivo in problemas:
        print("  [" + nombre + "]", repr(contenido[:70]), rect, "->", motivo)
    return 1


if __name__ == "__main__":
    sys.exit(main())
