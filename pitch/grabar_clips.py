# grabar_clips.py
# Paso 1 del video del pitch: juega STAR FORGE de verdad (sin ventana) y guarda "clips"
# (cuadros de 640x360 a 30 fps + los sonidos que el juego habría tocado) en pitch/_clips/.
# Paso 2: montar_video.py corta y une esos clips con la voz, la música y los subtítulos.
#
#   py -3.14 pitch/grabar_clips.py
#
# No modifica ningún archivo del juego. Requiere pygame.

import os
import pickle
import sys
import zlib

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

CARPETA = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(CARPETA)
CLIPS = os.path.join(CARPETA, "_clips")
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

import pygame

pygame.init()
pygame.display.set_mode((1280, 720))

import app
import nucleo
from interfaz import config, laboratorio, sonido

FPS = 30
DT = 1.0 / FPS


class Grabador:
    def __init__(self):
        self.ui = app.crear_ui()
        self.lienzo = pygame.Surface((config.ANCHO, config.ALTO))
        self.nombre = None          # clip que se está grabando (None = no se graba)
        self.cuadros = []
        self.sonidos = []           # (cuadro, nombre)
        self.marcas = {}            # nombre -> cuadro
        sonido.tocar = self.oir     # en vez de sonar, se anota cuándo sonó

    def oir(self, nombre):
        if self.nombre is not None:
            self.sonidos.append((len(self.cuadros), nombre))

    def clip(self, nombre):
        """Cierra el clip actual (lo guarda) y empieza otro. clip(None) = dejar de grabar."""
        if self.nombre is not None:
            datos = {"cuadros": self.cuadros, "sonidos": self.sonidos, "marcas": self.marcas}
            with open(os.path.join(CLIPS, self.nombre + ".pkl"), "wb") as f:
                pickle.dump(datos, f)
            print("  clip %-14s %4d cuadros (%.1f s)  marcas=%s" % (
                self.nombre, len(self.cuadros), len(self.cuadros) / FPS, self.marcas), flush=True)
        self.nombre = nombre
        self.cuadros, self.sonidos, self.marcas = [], [], {}

    def marca(self, nombre):
        self.marcas[nombre] = len(self.cuadros)

    def paso(self, dx=0, dy=0):
        app.dibujar_cuadro(self.lienzo, self.ui, app.textos_juego, dx, dy, DT)
        self.ui["tiempo"] += DT
        if self.nombre is not None:
            self.cuadros.append(zlib.compress(pygame.image.tobytes(self.lienzo, "RGB"), 1))

    def seg(self, segundos, dx=0, dy=0):
        for _ in range(round(segundos * FPS)):
            self.paso(dx, dy)

    def accion(self, nombre, valor=None):
        app.aplicar_accion(self.ui, nombre, valor)

    def caminar_a(self, x, y, max_seg=3.0):
        lab = self.ui["lab"]
        for _ in range(int(max_seg * FPS)):
            ex, ey = x - lab["x"], y - lab["y"]
            if abs(ex) <= 3 and abs(ey) <= 3:
                break
            dx = 0 if abs(ex) <= 3 else (1 if ex > 0 else -1)
            dy = 0 if abs(ey) <= 3 else (1 if ey > 0 else -1)
            self.paso(dx, dy)

    def teclear(self, texto, pausa=0.16):
        caja = self.ui["lab"]["caja"]
        caja.texto = ""
        self.seg(0.3)
        for ch in texto:
            caja.texto += ch
            self.seg(pausa)

    def hasta_resultados(self):
        while self.ui["pantalla"] == "simulacion":
            self.paso()


def y_estacion(ui, clave):
    return {c: y for c, x, y in laboratorio.posiciones_estaciones(ui["estado"])}[clave]


def optimos(mision_id):
    p = nucleo.cargar_parametros(mision_id)
    return {r["clave"]: "%g" % r["optimo"] for r in p["recursos"]}


def sesion_easy(g):
    ui = g.ui
    # --- Título: se escribe el callsign ---
    g.clip("titulo")
    g.seg(1.2)
    for ch in "ORION":
        ui["caja_nombre"].texto += ch
        g.seg(0.18)
    g.seg(1.5)
    g.accion("jugar")
    # --- Avatar ---
    g.clip("avatar")
    g.seg(0.5)
    for _ in range(6):
        g.accion("avatar_aleatorio")
        g.seg(0.42)
    g.seg(0.4)
    g.accion("avatar_listo")
    g.clip("bienvenida")
    g.seg(1.5)
    g.accion("cerrar_notificacion")
    # --- Parrilla: se recorren las 5 misiones ---
    g.clip("misiones")
    ids = [f["id"] for f in nucleo.cargar_misiones(ui["progreso"])]
    for mid in ids:
        g.accion("ver_mision", mid)
        g.seg(0.5)
    g.accion("ver_mision", "easy_cubesat")
    g.seg(0.6)
    g.accion("ir_info")
    g.clip("info")
    g.seg(1.6)
    g.accion("correr")
    g.clip("didactica")
    g.seg(2.2)
    g.accion("empezar_diseno")
    # --- Laboratorio: CML 1 y puertas del hangar ---
    g.clip("lab1")
    g.seg(0.4)
    g.caminar_a(196, 62, 2.0)
    g.marca("briefing")
    g.accion("abrir_briefing")
    g.seg(1.0)
    g.marca("puertas")
    g.accion("confirmar_briefing")
    g.seg(1.9)
    g.marca("pistas")
    g.seg(1.0)
    g.clip(None)
    g.accion("pistas_siguiente")
    g.accion("aceptar_pistas")
    # --- Estaciones: estructura (muy poca: fallará) y propulsión ---
    g.clip("lab2")
    g.caminar_a(305, y_estacion(ui, "estructura"), 2.5)
    g.marca("abre1")
    g.accion("abrir_estacion", "estructura")
    g.teclear("4")
    g.seg(0.7)
    g.marca("confirma1")
    g.accion("confirmar_estacion")
    g.seg(1.9)
    g.caminar_a(305, y_estacion(ui, "propulsion"), 2.5)
    g.marca("abre2")
    g.accion("abrir_estacion", "propulsion")
    g.teclear("400")
    g.seg(0.7)
    g.marca("confirma2")
    g.accion("confirmar_estacion")
    g.seg(1.9)
    g.clip("revision")
    g.accion("abrir_revision")
    g.seg(1.6)
    g.accion("confirmar_lanzamiento")
    g.clip("sim_falla")
    g.hasta_resultados()
    g.clip("res_falla")
    g.seg(4.5)
    print("  falla:", ui["revelado"]["exito"], ui["revelado"]["falla"])
    # --- TRY AGAIN: se corrige la estructura ---
    g.accion("reintentar")
    g.clip("lab_fix")
    g.seg(0.5)
    g.marca("abre")
    g.accion("abrir_estacion", "estructura")
    g.teclear("8.5", 0.2)
    g.seg(0.7)
    g.marca("confirma")
    g.accion("confirmar_estacion")
    g.seg(1.9)
    g.marca("revision")
    g.accion("abrir_revision")
    g.seg(1.5)
    g.accion("confirmar_lanzamiento")
    g.clip("sim_exito")
    g.hasta_resultados()
    g.clip("res_exito")
    g.seg(5.0)
    r = ui["revelado"]
    print("  éxito:", r["exito"], r["puntaje"], r["estrellas"])
    g.clip(None)


def sesion_rapida(g, mision_id, sufijo):
    """Otra misión con su reparto óptimo: hangar armándose, simulación y resultados."""
    ui = g.ui
    nucleo.DESBLOQUEO_EN_ORDEN = False
    g.accion("volver_misiones")
    g.accion("cerrar_notificacion")
    g.accion("ver_mision", mision_id)
    g.accion("ir_info")
    g.clip("info_" + sufijo)
    g.seg(1.5)
    g.accion("correr")
    g.clip("didactica_" + sufijo)
    g.seg(1.8)
    g.clip(None)
    g.accion("empezar_diseno")
    g.accion("abrir_briefing")
    g.accion("confirmar_briefing")
    g.seg(config.DURACION_CORTINAS + 0.3)
    g.accion("pistas_siguiente")
    g.accion("aceptar_pistas")
    g.clip("hangar_" + sufijo)
    g.seg(0.3)
    for clave, texto in optimos(mision_id).items():
        g.accion("abrir_estacion", clave)
        ui["lab"]["caja"].texto = texto
        g.accion("confirmar_estacion")
        g.seg(0.45)
    g.seg(1.8)
    g.clip(None)
    g.accion("abrir_revision")
    g.seg(0.1)
    g.accion("confirmar_lanzamiento")
    g.clip("sim_" + sufijo)
    g.hasta_resultados()
    g.clip("res_" + sufijo)
    g.seg(4.0)
    r = ui["revelado"]
    print("  %s: éxito=%s puntaje=%s estrellas=%s" % (mision_id, r["exito"], r["puntaje"], r["estrellas"]))
    g.clip(None)


def main():
    os.makedirs(CLIPS, exist_ok=True)
    g = Grabador()
    print("Easy...", flush=True)
    sesion_easy(g)
    print("Mars rover...", flush=True)
    sesion_rapida(g, "harder_perseverance", "marte")
    print("Moon orbiter...", flush=True)
    sesion_rapida(g, "insane_artemis1", "luna")
    print("Mars orbiter...", flush=True)
    sesion_rapida(g, "hard_mro_marte", "mro")
    print("LISTO", flush=True)


if __name__ == "__main__":
    main()
