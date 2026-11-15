# montar_video.py
# Paso 2 del video del pitch de STAR FORGE (30 s): une los clips grabados por grabar_clips.py
# con la voz de Justin (pitch/voz_justin.ogg), música sintetizada por código (sin copyright),
# los sonidos del propio juego (interfaz/sonido.py) y subtítulos en inglés.
#
#   py -3.14 pitch/grabar_clips.py     (una vez, o cuando cambie el juego)
#   py -3.14 pitch/montar_video.py     -> pitch/star_forge_pitch.mp4  (1920x1080, 30 fps)
#
# Para ajustar el montaje: TOMAS (qué clip se ve en cada segundo) y SUBTITULOS.
# Requiere: pygame, numpy, imageio-ffmpeg. No modifica ningún archivo del juego.

import os
import pickle
import subprocess
import sys
import wave
import zlib

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

CARPETA = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(CARPETA)
CLIPS = os.path.join(CARPETA, "_clips")
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

import numpy as np
import pygame
import imageio_ffmpeg

pygame.init()
pygame.display.set_mode((1280, 720))

from interfaz import config, estilo, sprites, sonido

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
FPS = 30
SR = 44100
ANCHO, ALTO = 1920, 1080               # 640x360 x3, sin suavizar
DURACION = 29.6                        # el reto exige MÁXIMO 30 s
VOZ = os.path.join(CARPETA, "voz_justin.ogg")
DESFASE_VOZ = 0.25                     # segundo del video en que empieza el audio de la voz
SALIDA = os.path.join(CARPETA, "star_forge_pitch.mp4")
T_FINAL = 27.0                         # empieza la tarjeta final

# (segundo del video, clip, cuadro inicial del clip, velocidad, palabra grande o None)
TOMAS = [
    (0.00, "avatar", 15, 1.0, None),            # "Today's generation grows up playing."
    (2.40, "lab1", 0, 1.0, None),               # "Can we turn playing into scientific curiosity?"
    (4.45, "titulo", 9, 1.0, None),             # "Hi, we are Aion Space and this is Star Forge:"
    (7.42, "hangar_luna", 20, 1.6, "BUILD"),    # "build,"
    (8.00, "lab2", 184, 1.0, "BALANCE"),        # "balance,"
    (8.58, "sim_marte", 108, 1.5, "LAUNCH"),    # "launch."
    (9.60, "misiones", 15, 2.0, None),          # "Build rockets with real NASA data,"
    (10.60, "didactica_marte", 8, 1.0, None),
    (11.45, "lab2", 45, 1.0, None),             # "but engineering and budget must stay in balance."
    (12.65, "lab2", 82, 1.0, None),
    (13.30, "revision", 6, 1.0, None),
    (14.10, "sim_falla", 196, 1.6, None),       # "When a mission fails,"
    (15.40, "res_falla", 0, 1.0, None),         # "the game shows whether design or budget was the problem."
    (18.45, "lab_fix", 15, 1.6, None),          # "What if the next aerospace engineer..."
    (19.35, "sim_exito", 232, 1.5, None),
    (20.35, "sim_exito", 300, 1.0, None),
    (20.90, "res_exito", 30, 1.0, None),        # "...is born playing Star Forge?"
    (22.20, "sim_marte", 262, 2.0, None),       # "A generation that learns space science through playing,"
    (23.75, "sim_luna", 244, 1.5, None),
    (25.05, "sim_mro", 268, 1.5, None),         # "and one day will be able to build real missions."
    (26.00, "sim_marte", 366, 1.0, None),
]

# (inicio, fin, texto) en segundos DEL AUDIO de la voz (se les suma DESFASE_VOZ)
SUBTITULOS = [
    (0.10, 2.05, "Today's generation grows up playing."),
    (2.20, 4.15, "Can we turn playing into scientific curiosity?"),
    (4.25, 7.10, "Hi, we are Aion Space and this is Star Forge:"),
    (7.18, 9.20, "build, balance, launch."),
    (9.50, 11.15, "Build rockets with real NASA data,"),
    (11.22, 13.70, "but engineering and budget must stay in balance."),
    (13.90, 15.00, "When a mission fails,"),
    (15.15, 17.95, "the game shows whether design or budget was the problem."),
    (18.22, 21.60, "What if the next aerospace engineer is born playing Star Forge?"),
    (21.95, 28.10, "A generation that learns space science through playing, and one day will be able to build real missions."),
]

_clips = {}


def clip(nombre):
    if nombre not in _clips:
        with open(os.path.join(CLIPS, nombre + ".pkl"), "rb") as f:
            _clips[nombre] = pickle.load(f)
    return _clips[nombre]


def toma_en(t):
    """Índice de la toma que se ve en el segundo t."""
    i = 0
    for k in range(len(TOMAS)):
        if TOMAS[k][0] <= t + 1e-9:
            i = k
    return i


def fin_toma(i):
    return TOMAS[i + 1][0] if i + 1 < len(TOMAS) else T_FINAL + 0.4


# ---------------------------------------------------------------------------
# Video
# ---------------------------------------------------------------------------

def cuadro_de_toma(lienzo, i, t):
    inicio, nombre, f0, vel, palabra = TOMAS[i]
    cuadros = clip(nombre)["cuadros"]
    k = min(len(cuadros) - 1, f0 + int((t - inicio) * FPS * vel))
    img = pygame.image.frombytes(zlib.decompress(cuadros[k]), (config.ANCHO, config.ALTO), "RGB")
    lienzo.blit(img, (0, 0))
    if palabra:
        # Palabra grande estilo arcade, con un pequeño "salto" al entrar.
        salto = max(0, 6 - int((t - inicio) * 60))
        velo = pygame.Surface((config.ANCHO, 64), pygame.SRCALPHA)
        velo.fill((8, 8, 16, 170))
        lienzo.blit(velo, (0, 203))
        cx, cy = config.ANCHO // 2, 235 - salto
        estilo.texto_contorno(lienzo, palabra, cx + 3, cy + 3, config.LETRA_GIGANTE, config.ROJO, config.NEGRO, 2)
        estilo.texto_contorno(lienzo, palabra, cx, cy, config.LETRA_GIGANTE, config.AMARILLO, config.NEGRO, 2)


def tarjeta_final(lienzo, t):
    estilo.fondo_estrellas(lienzo, t)
    sprites.dibujar_tierra_y_cohete(lienzo, t - T_FINAL + 0.8)
    cx = config.ANCHO // 2
    estilo.texto_contorno(lienzo, "STAR FORGE", cx + 3, 63, config.LETRA_GIGANTE, config.ROJO, config.NEGRO, 2)
    estilo.texto_contorno(lienzo, "STAR FORGE", cx, 60, config.LETRA_GIGANTE, config.AMARILLO, config.NEGRO, 2)
    estilo.texto(lienzo, "Build. Balance. Launch.", cx, 102, config.LETRA_NORMAL, config.CIAN, centrado=True)
    estilo.texto(lienzo, "Team Aion Space", cx, 150, config.LETRA_NORMAL, config.BLANCO, centrado=True)
    estilo.texto(lienzo, "NASA Space Apps Challenge 2026", cx, 172, config.LETRA_PEQUENA,
                 config.COLOR_TEXTO_SUAVE, centrado=True)


class Subtitulos:
    def __init__(self):
        try:
            self.fuente = pygame.font.SysFont("arial", 56, bold=True)
        except Exception:
            self.fuente = pygame.font.Font(None, 60)

    def partir(self, texto, ancho):
        lineas, actual = [], ""
        for p in texto.split():
            prueba = (actual + " " + p).strip()
            if self.fuente.size(prueba)[0] > ancho and actual:
                lineas.append(actual)
                actual = p
            else:
                actual = prueba
        lineas.append(actual)
        return lineas

    def dibujar(self, sup, t):
        for a, b, texto in SUBTITULOS:
            if a + DESFASE_VOZ - 0.05 <= t < b + DESFASE_VOZ + 0.1:
                lineas = self.partir(texto, 1640)
                alto_linea = 70
                y0 = ALTO - 40 - alto_linea * len(lineas)
                ancho = max(self.fuente.size(l)[0] for l in lineas) + 60
                caja = pygame.Surface((ancho, alto_linea * len(lineas) + 16), pygame.SRCALPHA)
                caja.fill((0, 0, 0, 175))
                sup.blit(caja, ((ANCHO - ancho) // 2, y0 - 8))
                for k, linea in enumerate(lineas):
                    cy = y0 + alto_linea // 2 + alto_linea * k
                    borde = self.fuente.render(linea, True, (0, 0, 0))
                    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                        sup.blit(borde, borde.get_rect(center=(ANCHO // 2 + dx, cy + dy)))
                    img = self.fuente.render(linea, True, (255, 255, 255))
                    sup.blit(img, img.get_rect(center=(ANCHO // 2, cy)))
                return


def hacer_video(ruta):
    cmd = [FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (ANCHO, ALTO),
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-pix_fmt", "yuv420p",
           "-crf", "15", ruta]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    lienzo = pygame.Surface((config.ANCHO, config.ALTO))
    otro = pygame.Surface((config.ANCHO, config.ALTO))
    grande = pygame.Surface((ANCHO, ALTO))
    negro = pygame.Surface((ANCHO, ALTO))
    subs = Subtitulos()
    total = round(DURACION * FPS)
    for n in range(total):
        t = n / FPS
        if t < T_FINAL:
            cuadro_de_toma(lienzo, toma_en(t), t)
        else:
            tarjeta_final(lienzo, t)
            if t < T_FINAL + 0.4:                       # fundido desde la última toma
                cuadro_de_toma(otro, len(TOMAS) - 1, t)
                otro.set_alpha(int(255 * (1 - (t - T_FINAL) / 0.4)))
                lienzo.blit(otro, (0, 0))
        pygame.transform.scale(lienzo, (ANCHO, ALTO), grande)
        subs.dibujar(grande, t)
        oscuro = 0.0
        if t < 0.3:
            oscuro = 1 - t / 0.3
        elif t > DURACION - 0.35:
            oscuro = (t - (DURACION - 0.35)) / 0.35
        if oscuro > 0:
            negro.set_alpha(int(255 * min(1.0, oscuro)))
            grande.blit(negro, (0, 0))
        proc.stdin.write(pygame.image.tobytes(grande, "RGB"))
    proc.stdin.close()
    proc.wait()


# ---------------------------------------------------------------------------
# Audio
# ---------------------------------------------------------------------------

def leer_voz():
    filtro = "highpass=f=85,acompressor=threshold=-20dB:ratio=3:attack=10:release=150:makeup=2"
    cmd = [FFMPEG, "-v", "error", "-i", VOZ, "-af", filtro, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"]
    v = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, dtype=np.float32).copy()
    return v / max(np.max(np.abs(v)), 1e-6) * 0.92


def tono(freq, dur, ataque, caida, armonicos=(1.0, 0.3, 0.15)):
    t = np.arange(int(dur * SR)) / SR
    onda = sum(a * np.sin(2 * np.pi * freq * (k + 1) * t) for k, a in enumerate(armonicos))
    env = np.minimum(1.0, t / ataque) * np.clip((dur - t) / caida, 0, 1)
    return onda * env


def poner(pista, inicio_s, muestras, ganancia=1.0):
    a = int(inicio_s * SR)
    if a >= len(pista) or a < 0:
        return
    b = min(len(pista), a + len(muestras))
    pista[a:b] += muestras[:b - a] * ganancia


def construir_musica():
    """Pad Am-F-C-G (4 s por acorde, 120 bpm). Entra por capas: pad, arpegio (al aparecer
    el título) y pulso de bajo + bombo suave (desde "build, balance, launch")."""
    n = int(DURACION * SR)
    pista = np.zeros(n)
    acordes = [(110.0, 220.0, 261.63, 329.63), (87.31, 174.61, 261.63, 349.23),
               (130.81, 196.0, 261.63, 329.63), (98.0, 196.0, 246.94, 293.66)]
    arpegios = [[440.0, 523.25, 659.25, 523.25], [349.23, 440.0, 523.25, 440.0],
                [392.0, 523.25, 659.25, 523.25], [392.0, 493.88, 587.33, 493.88]]
    rng = np.random.default_rng(3)
    for i in range(8):
        t0 = i * 4.0
        c = i % 4
        if t0 >= 24.0:
            c = 2 if t0 >= 28.0 else c                    # termina en Do (resuelve)
        for f in acordes[c]:
            poner(pista, t0, tono(f, 5.2, 1.0, 1.4), 0.22)
        for j in range(8):
            tj = t0 + j * 0.5
            if 4.5 <= tj < 27.0:
                f = arpegios[c][j % 4]
                tt = np.arange(int(0.9 * SR)) / SR
                poner(pista, tj, np.sin(2 * np.pi * f * tt) * np.exp(-tt * 5.5), 0.13)
                poner(pista, tj + 0.25, np.sin(2 * np.pi * f * 2 * tt) * np.exp(-tt * 9), 0.04)
            if 7.4 <= tj < 27.0:
                tt = np.arange(int(0.3 * SR)) / SR
                bombo = np.sin(2 * np.pi * (45 * tt + 40 * (1 - np.exp(-tt * 30)) / 30)) * np.exp(-tt * 14)
                poner(pista, tj, bombo, 0.42)
                bajo = np.sin(2 * np.pi * acordes[c][0] / 2 * 2 * tt) * np.exp(-tt * 9)
                poner(pista, tj + 0.25, bajo, 0.20)
                tic = rng.normal(size=int(0.04 * SR)) * np.exp(-np.arange(int(0.04 * SR)) / (0.008 * SR))
                poner(pista, tj + 0.25, tic, 0.035)
    # Acorde final que crece con la tarjeta de cierre
    for f in (130.81, 196.0, 261.63, 329.63, 523.25):
        poner(pista, T_FINAL - 0.3, tono(f, 3.2, 0.5, 2.2), 0.22)
    return pista / np.max(np.abs(pista))


def sonidos_del_juego():
    """Coloca los sonidos que el juego tocó en cada toma (mismos sonidos de interfaz/sonido.py)."""
    recetas = {"pitido": sonido.crear_pitido, "pitido_final": sonido.crear_pitido_final,
               "ignicion": sonido.crear_ignicion, "exito": sonido.crear_exito,
               "falla": sonido.crear_falla, "explosion": sonido.crear_explosion,
               "puertas": sonido.crear_puertas, "clic": sonido.crear_clic}
    banco = {k: np.repeat(np.array(f(), dtype=np.float64), SR // sonido.FRECUENCIA) for k, f in recetas.items()}
    volumen = {"explosion": 0.34, "ignicion": 0.26, "exito": 0.20, "falla": 0.12, "clic": 0.16,
               "pitido": 0.10, "pitido_final": 0.10, "puertas": 0.14}
    pista = np.zeros(int(DURACION * SR))
    for i, (inicio, nombre, f0, vel, _) in enumerate(TOMAS):
        fin = fin_toma(i)
        f1 = f0 + (fin - inicio) * FPS * vel
        for f, s in clip(nombre)["sonidos"]:
            muestras = banco[s]
            if f0 <= f < f1:
                t = inicio + (f - f0) / (FPS * vel)
            elif s == "ignicion" and f < f0 and (f0 - f) / FPS < len(muestras) / SR - 0.3:
                muestras = muestras[int((f0 - f) / FPS * SR):]        # el rugido ya venía sonando
                t = inicio
            else:
                continue
            largo = min(len(muestras), int((fin + 0.35 - t) * SR))   # se corta poco después del cambio de toma
            if largo <= 0:
                continue
            trozo = muestras[:largo].copy()
            cola = min(largo, int(0.3 * SR))
            trozo[-cola:] *= np.linspace(1, 0, cola)
            poner(pista, t, trozo, volumen[s])
    return pista


def hacer_audio(ruta):
    n = int(DURACION * SR)
    voz = np.zeros(n)
    poner(voz, DESFASE_VOZ, leer_voz())
    ventana = int(0.25 * SR)
    energia = np.convolve(np.abs(voz), np.ones(ventana) / ventana, mode="same")
    ganancia = 1.0 - 0.5 * np.clip(energia / 0.05, 0, 1)             # la música baja cuando habla la voz
    musica = construir_musica()[:n] * ganancia * 0.17
    k = np.arange(n)
    musica *= np.minimum(1.0, k / (0.8 * SR)) * np.minimum(1.0, (n - k) / (1.2 * SR))
    mezcla = voz + musica + sonidos_del_juego()[:n] * 0.9
    pico = np.max(np.abs(mezcla))
    if pico > 0.97:
        mezcla = mezcla / pico * 0.97
    with wave.open(ruta, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mezcla * 32767).astype(np.int16).tobytes())


def main():
    sin_audio = os.path.join(CARPETA, "_video.mp4")
    audio = os.path.join(CARPETA, "_audio.wav")
    print("Video...", flush=True)
    hacer_video(sin_audio)
    print("Audio...", flush=True)
    hacer_audio(audio)
    subprocess.run([FFMPEG, "-y", "-v", "error", "-i", sin_audio, "-i", audio, "-c:v", "copy",
                    "-af", "loudnorm=I=-15:TP=-1.5:LRA=11", "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-t", str(DURACION), "-movflags", "+faststart",
                    "-metadata", "title=STAR FORGE - Team Aion Space - NASA Space Apps Challenge 2026",
                    "-metadata", "comment=Real gameplay capture. Voice: team member. Music and sound effects "
                                 "synthesized by code. Editing script written with AI assistance (Claude).",
                    SALIDA], check=True)
    os.remove(sin_audio)
    os.remove(audio)
    print("Listo:", SALIDA)


if __name__ == "__main__":
    main()
