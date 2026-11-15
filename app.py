# app.py
# Punto de entrada de STAR FORGE. Ejecutar con:  python3.12 app.py
#
# Aquí están:
#   1. La lectura de los textos en inglés (interfaz/textos_en.json y, desde la v2,
#      interfaz/guia_misiones_en.json, que queda en textos["guia"]).
#   2. El diccionario "ui" con el estado de la interfaz.
#   3. aplicar_accion(): qué pasa cuando se clica cada botón. Solo llama a
#      funciones de nucleo.py (ver CONTRATO_API.md); aquí no hay reglas del juego.
#   4. El bucle principal de Pygame: leer eventos -> dibujar -> mostrar.
#
# Estilo 16 bits: todo se dibuja en una superficie pequeña de 640x360 ("lienzo") y
# al final se agranda ESCALA veces a la ventana real, sin suavizar.
#
# Flujo de pantallas (v2):
#   inicio -> avatar -> misiones -> info_mision -> didactica -> laboratorio -> simulacion -> resultados
#     |                    ^                                                                  |
#     +-> creditos         +------------------ "Back to missions" / "Try again" -------------+
#   En el laboratorio y en la pantalla didáctica, Esc abre el menú de pausa (interfaz/pausa.py).
#   Enter activa el botón principal de cada pantalla o ventana.

import json
import random
import sys

import pygame

import nucleo
from interfaz import config, sonido, sprites
from interfaz import (pantalla_inicio, pantalla_avatar, pantalla_misiones, pantalla_info,
                      pantalla_didactica, laboratorio, simulacion, resultados, notificaciones,
                      pausa, pantalla_creditos)
from interfaz.componentes import CajaTexto, boton_principal

# Qué módulo dibuja cada pantalla.
PANTALLAS = {
    "inicio": pantalla_inicio,
    "avatar": pantalla_avatar,
    "misiones": pantalla_misiones,
    "info_mision": pantalla_info,
    "didactica": pantalla_didactica,
    "laboratorio": laboratorio,
    "simulacion": simulacion,
    "resultados": resultados,
    "creditos": pantalla_creditos,
}

# Pantallas donde Esc abre el menú de pausa.
PANTALLAS_CON_PAUSA = ("laboratorio", "didactica")


# ---------------------------------------------------------------------------
# 1. Textos
# ---------------------------------------------------------------------------

def cargar_json(ruta):
    """Lee un archivo JSON. encoding="utf-8" porque hay tildes (órbita)."""
    with open(ruta, encoding="utf-8") as archivo:
        return json.load(archivo)


def cargar_textos():
    """textos_en.json + la guía de la v2 dentro de textos["guia"]."""
    textos = cargar_json(config.RUTA_TEXTOS)
    textos["guia"] = cargar_json(config.RUTA_GUIA)
    return textos


# Los textos se leen una sola vez al empezar. aplicar_accion los usa para los
# mensajes del asistente.
textos_juego = cargar_textos()


# ---------------------------------------------------------------------------
# 2. Estado de la interfaz
# ---------------------------------------------------------------------------

def crear_ui():
    """Diccionario con todo lo que la interfaz necesita recordar."""
    return {
        "pantalla": "inicio",                 # qué pantalla se ve
        "tiempo": 0.0,                        # segundos desde que empezó el juego (animaciones)
        "jugador": {"nombre": config.NOMBRE_POR_DEFECTO, "avatar": sprites.avatar_inicial()},
        "caja_nombre": CajaTexto(config.ANCHO // 2 - 80, 164, 160, 24,
                                 maximo=config.MAX_LETRAS_NOMBRE),
        "progreso": nucleo.nuevo_progreso(),  # misiones completadas (se crea una sola vez)
        "mision_vista": None,                 # misión resaltada en la parrilla
        "mision_id": None,                    # misión que se juega, p. ej. "easy_cubesat"
        "mision_nombre": "",                  # nombre en inglés, para los títulos
        "ficha": None,                        # datos de la ficha de misión (se leen una vez)
        "estado": None,                       # estado de nucleo.iniciar_mision()
        "lab": None,                          # sub-estado del laboratorio
        "sim": None,                          # sub-estado de la simulación (con el resultado)
        "revelado": None,                     # lo que devolvió nucleo.revelar()
        "notificaciones": [],                 # cola de mensajes del asistente (notificaciones.py)
        "vio_bienvenida": False,              # la bienvenida de la parrilla sale una sola vez
        "aviso_parrilla": None,               # mensaje para cuando se vuelva a la parrilla
        "pagina_didactica": 0,                # página de recursos en la pantalla didáctica
        "pausa": False,                       # True = menú de pausa abierto
        "ver_creditos": False,                # True = se acaba de completar la última misión
        "creditos_vuelta": "inicio",          # a qué pantalla se vuelve desde los créditos
    }


def empezar_mision(ui):
    """Crea una misión nueva de ui["mision_id"], desde CML 1 y sin nada repartido."""
    parametros = nucleo.cargar_parametros(ui["mision_id"])
    ui["estado"] = nucleo.iniciar_mision(parametros)
    ui["lab"] = laboratorio.nuevo_lab()
    ui["sim"] = None
    ui["revelado"] = None
    ui["pausa"] = False


def reintentar_mision(ui):
    """TRY AGAIN (v2, punto 2): misión nueva, pero cada estación conserva la cantidad
    que el jugador escribió antes. El reparto se rehace con cotizar + repartir."""
    escrito = {}
    if ui["lab"] is not None:
        escrito = dict(ui["lab"]["escrito"])
    empezar_mision(ui)
    laboratorio.conservar_reparto(ui["lab"], ui["estado"], escrito, ui["tiempo"])


def elegir_mision(ui, mision_id):
    """Guarda la misión elegida en la parrilla y su nombre en inglés."""
    ui["mision_id"] = mision_id
    for fila in nucleo.cargar_misiones(ui["progreso"]):
        if fila["id"] == mision_id:
            ui["mision_nombre"] = fila["nombre"]


def avatar_aleatorio(avatar):
    """Elige una opción al azar en cada categoría."""
    for categoria in avatar:
        avatar[categoria] = random.randrange(sprites.CANTIDAD_OPCIONES[categoria])


def ir_a_misiones(ui):
    """Vuelve a la parrilla y, si hay, muestra el aviso pendiente del asistente."""
    ui["pantalla"] = "misiones"
    ui["pausa"] = False
    if ui["aviso_parrilla"] is not None:         # "New mission unlocked" o un consejo
        texto, expresion = ui["aviso_parrilla"]
        notificaciones.mostrar_notificacion(ui, texto, expresion)
        ui["aviso_parrilla"] = None


def ir_a_creditos(ui, vuelta):
    """Pantalla de créditos; 'vuelta' es la pantalla a la que se vuelve después."""
    ui["creditos_t0"] = ui["tiempo"]
    ui["creditos_vuelta"] = vuelta
    ui["pantalla"] = "creditos"


# ---------------------------------------------------------------------------
# 3. Qué hace cada botón (o tecla)
# ---------------------------------------------------------------------------

def aplicar_accion(ui, accion, valor):
    """Cambia "ui" según la acción. "valor" es el dato extra del botón."""
    # Primero, el menú de pausa (si está abierto) y las acciones propias del laboratorio.
    if pausa.aplicar(ui, accion):
        return
    if ui["pantalla"] == "laboratorio" and laboratorio.aplicar(ui, accion, valor):
        return

    if accion == "jugar":
        nombre = ui["caja_nombre"].texto.strip()
        if nombre == "":
            nombre = config.NOMBRE_POR_DEFECTO
        ui["jugador"]["nombre"] = nombre
        ui["pantalla"] = "avatar"

    elif accion == "selector":
        # valor = (categoria, -1 o +1). El % hace que después de la última vuelva a la primera.
        categoria, paso = valor
        avatar = ui["jugador"]["avatar"]
        avatar[categoria] = (avatar[categoria] + paso) % sprites.CANTIDAD_OPCIONES[categoria]

    elif accion == "elegir_opcion":
        # valor = (categoria, indice): clic en una muestra de color.
        categoria, indice = valor
        ui["jugador"]["avatar"][categoria] = indice

    elif accion == "avatar_aleatorio":
        avatar_aleatorio(ui["jugador"]["avatar"])

    elif accion == "avatar_listo":
        ui["pantalla"] = "misiones"
        if not ui["vio_bienvenida"]:                 # frase del asistente (sección 7.3)
            ui["vio_bienvenida"] = True
            notificaciones.mostrar_notificacion(ui, textos_juego["notificaciones"]["bienvenida"],
                                                "feliz", duracion=9)

    elif accion == "ir_avatar":
        ui["pantalla"] = "avatar"

    elif accion == "ver_mision":
        ui["mision_vista"] = valor           # valor = id de la misión

    elif accion == "ir_info":
        # Solo se entra si el núcleo deja jugar esa misión.
        if nucleo.puede_jugar(ui["progreso"], ui["mision_vista"]):
            elegir_mision(ui, ui["mision_vista"])
            ui["pantalla"] = "info_mision"

    elif accion == "volver_misiones":
        # Al completar la última misión (Insane), primero se ven los créditos.
        if ui["pantalla"] == "resultados" and ui["ver_creditos"]:
            ui["ver_creditos"] = False
            ir_a_creditos(ui, "misiones")
        else:
            ir_a_misiones(ui)

    elif accion == "cerrar_notificacion":
        notificaciones.cerrar(ui)

    elif accion == "correr":
        # RUN: primero la pantalla didáctica con AION (v2, punto 3)
        ui["pagina_didactica"] = 0
        ui["pausa"] = False
        ui["pantalla"] = "didactica"

    elif accion == "pagina_didactica":
        ui["pagina_didactica"] = ui["pagina_didactica"] + valor     # valor = -1 o +1

    elif accion == "volver_info":
        ui["pantalla"] = "info_mision"

    elif accion == "empezar_diseno":
        # LET'S DESIGN: misión nueva y al laboratorio
        empezar_mision(ui)
        ui["pantalla"] = "laboratorio"

    elif accion == "confirmar_lanzamiento":
        # revisar() ya dio ok: simulamos AHORA y guardamos el resultado sin mostrarlo.
        resultado = nucleo.simular(ui["estado"])
        ui["sim"] = simulacion.nueva_sim(resultado, ui["tiempo"])
        ui["pantalla"] = "simulacion"

    elif accion == "reintentar":
        reintentar_mision(ui)
        ui["pantalla"] = "laboratorio"

    elif accion == "ver_creditos":
        ir_a_creditos(ui, ui["pantalla"])

    elif accion == "salir_creditos":
        if ui["creditos_vuelta"] == "misiones":
            ir_a_misiones(ui)
        else:
            ui["pantalla"] = ui["creditos_vuelta"]

    # Acciones del menú de pausa que cambian de pantalla (pausa.aplicar ya lo cerró)
    elif accion == "pausa_reiniciar":
        empezar_mision(ui)                    # desde CML 1, sin conservar nada
        ui["pantalla"] = "laboratorio"

    elif accion == "pausa_misiones":
        ir_a_misiones(ui)

    elif accion == "pausa_menu":
        ui["pantalla"] = "inicio"             # el progreso se mantiene


def desbloquear_todo(ui):
    """Tecla de depuración (F2): todas las misiones quedan disponibles mientras el juego
    está abierto. Usa la regla que ya tiene nucleo.cargar_misiones (DESBLOQUEO_EN_ORDEN)."""
    if nucleo.DESBLOQUEO_EN_ORDEN:
        nucleo.DESBLOQUEO_EN_ORDEN = False
        notificaciones.mostrar_notificacion(ui, textos_juego["notificaciones"]["depuracion"], "sorprendido", 3)


def misiones_jugables(ui):
    """Ids de las misiones que ya se pueden jugar (para saber cuál se acaba de desbloquear)."""
    return [fila["id"] for fila in nucleo.cargar_misiones(ui["progreso"])
            if fila["estado"] in ("disponible", "completada")]


def ir_a_resultados(ui):
    """Revela y registra el resultado UNA sola vez (así el progreso se guarda aunque
    luego pulse "Try again")."""
    ui["revelado"] = nucleo.revelar(ui["estado"])
    antes = misiones_jugables(ui)
    nucleo.registrar_resultado(ui["progreso"], ui["estado"])
    parrilla = nucleo.cargar_misiones(ui["progreso"])
    nuevas = [fila for fila in parrilla
              if fila["estado"] == "disponible" and fila["id"] not in antes]
    # Qué dirá el asistente al volver a la parrilla
    t = textos_juego["notificaciones"]
    if nuevas:
        ui["aviso_parrilla"] = (t["desbloqueo"].replace("{mision}", nuevas[0]["nombre"]), "sorprendido")
    elif not ui["revelado"]["exito"]:
        ui["aviso_parrilla"] = (t["reintento"], "preocupado")
    else:
        ui["aviso_parrilla"] = None
    # Completar la última misión de la parrilla (Insane) lleva a los créditos (v2, punto 13)
    ui["ver_creditos"] = ui["revelado"]["exito"] and ui["mision_id"] == parrilla[-1]["id"]
    ui["resultados_t0"] = ui["tiempo"]       # para animar estrellas y puntaje
    ui["pantalla"] = "resultados"


# ---------------------------------------------------------------------------
# 4. Bucle principal
# ---------------------------------------------------------------------------

def es_enter(evento):
    return evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER)


def tecla_pausa(ui, evento):
    """Esc abre o cierra el menú de pausa. Devuelve True si la tecla ya se usó."""
    if ui["pantalla"] not in PANTALLAS_CON_PAUSA:
        return False
    if ui["pausa"]:
        if evento.key == pygame.K_ESCAPE:
            ui["pausa"] = False
        return not es_enter(evento)           # Enter sigue: activa "Resume" (botón principal)
    if evento.key == pygame.K_ESCAPE:
        # En el laboratorio, Esc solo pausa si no hay una ventana abierta.
        if ui["pantalla"] == "laboratorio" and ui["lab"]["ventana"] is not None:
            return False
        ui["pausa"] = True
        return True
    return False


def procesar_tecla(ui, evento, botones):
    """Una tecla. Devuelve True si cambió algo (los botones del cuadro ya no sirven)."""
    if config.DEPURACION and evento.key == config.TECLA_DESBLOQUEAR:
        desbloquear_todo(ui)                     # F2: tecla de depuración (ver config.py)
        return False
    if evento.key == pygame.K_m and ui["pantalla"] != "inicio":
        sonido.alternar_silencio()               # M: silencio (v2, D11). En inicio se escribe el nombre.
        return False
    if tecla_pausa(ui, evento):
        return True
    if es_enter(evento) and notificaciones.hay_notificacion(ui):
        notificaciones.cerrar(ui)                # Enter también cierra la notificación de AION
    # Algunas pantallas usan el teclado (nombre, cantidades, E).
    modulo = PANTALLAS[ui["pantalla"]]
    if not ui["pausa"] and hasattr(modulo, "tecla"):
        respuesta = modulo.tecla(ui, evento)
        if respuesta is not None:
            aplicar_accion(ui, respuesta[0], respuesta[1])
            return True
    # Enter = botón principal de la pantalla o ventana (v2, punto 5)
    if es_enter(evento):
        boton = boton_principal(botones)
        if boton is not None:
            aplicar_accion(ui, boton.accion, boton.valor)
            return True
    return False


def procesar_eventos(ui, botones):
    """Lee mouse y teclado. Devuelve False si el jugador cerró la ventana."""
    hubo_cambio = False     # tras un clic la pantalla puede cambiar y los botones ya no sirven
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            return False
        if hubo_cambio:
            continue
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            # button == 1 es el clic izquierdo. La posición se pasa a coordenadas 640x360.
            posicion = (evento.pos[0] // config.ESCALA, evento.pos[1] // config.ESCALA)
            for boton in botones:
                if boton.fue_clicado(posicion):
                    aplicar_accion(ui, boton.accion, boton.valor)
                    hubo_cambio = True
                    break   # solo un botón por clic
        elif evento.type == pygame.KEYDOWN:
            hubo_cambio = procesar_tecla(ui, evento, botones)
    return True


def direccion_teclado():
    """(dx, dy) según las teclas que están APRETADAS ahora: flechas o WASD.
    dx: -1 izquierda, 1 derecha, 0 nada. dy: -1 arriba, 1 abajo, 0 nada."""
    teclas = pygame.key.get_pressed()
    dx = 0
    dy = 0
    if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
        dx = dx - 1
    if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
        dx = dx + 1
    if teclas[pygame.K_UP] or teclas[pygame.K_w]:
        dy = dy - 1
    if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
        dy = dy + 1
    return dx, dy


def dibujar_cuadro(lienzo, ui, textos, dx=0, dy=0, dt=0.0):
    """Un cuadro completo: actualiza, dibuja la pantalla y devuelve sus botones.
    Está separado de main() para poder probar el juego sin ventana."""
    # Las pantallas con movimiento (el laboratorio) se actualizan cada cuadro, salvo en pausa.
    modulo = PANTALLAS[ui["pantalla"]]
    if hasattr(modulo, "actualizar") and not ui["pausa"]:
        modulo.actualizar(ui, dx, dy, dt)

    botones = modulo.dibujar(lienzo, ui, textos)
    for boton in botones:
        boton.dibujar(lienzo)
    if ui["pausa"]:
        # Con la pausa abierta solo sirven sus botones.
        botones = pausa.dibujar(lienzo, ui, textos)
        for boton in botones:
            boton.dibujar(lienzo)
    sprites.dibujar_parlante(lienzo, config.ANCHO - 14, 3, sonido.silenciado())   # M = silencio
    # La notificación del asistente va encima de todo; su botón se revisa primero.
    botones = notificaciones.dibujar(lienzo, ui, textos) + botones

    # Si la animación de la simulación terminó, pasamos a resultados.
    if ui["pantalla"] == "simulacion" and ui["sim"]["terminada"]:
        ir_a_resultados(ui)
    return botones


def main():
    pygame.init()
    sonido.iniciar()      # sonidos generados por código; si no hay audio, el juego sigue mudo
    textos = textos_juego
    ventana = pygame.display.set_mode((config.ANCHO * config.ESCALA, config.ALTO * config.ESCALA))
    pygame.display.set_caption(textos["titulo_ventana"])
    lienzo = pygame.Surface((config.ANCHO, config.ALTO))    # aquí se dibuja todo
    reloj = pygame.time.Clock()

    ui = crear_ui()
    botones = []          # botones de la pantalla actual (los da cada pantalla)
    dt = 0.0              # segundos que duró el cuadro anterior
    jugando = True

    while jugando:
        # a) Leer lo que hizo el jugador.
        jugando = procesar_eventos(ui, botones)

        # b) Actualizar y dibujar la pantalla actual en el lienzo de 640x360.
        dx, dy = direccion_teclado()
        botones = dibujar_cuadro(lienzo, ui, textos, dx, dy, dt)

        # c) Agrandar el lienzo a la ventana (sin suavizar) y mostrarlo.
        pygame.transform.scale(lienzo, ventana.get_size(), ventana)
        pygame.display.flip()
        dt = min(reloj.tick(config.FPS) / 1000, config.DT_MAXIMO)    # ms -> s, con tope
        ui["tiempo"] = ui["tiempo"] + dt

    pygame.quit()
    sys.exit()


# Esto hace que main() solo se ejecute al correr "python3.12 app.py",
# y no cuando otro archivo hace "import app".
if __name__ == "__main__":
    main()
