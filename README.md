# Space Mission Design Game

Juego interactivo para el reto **Space Mission Design Game** del NASA Space Apps Challenge 2026. El jugador diseña, gestiona y simula una misión espacial completa tomando decisiones de ingeniería con recursos limitados (masa, potencia, costo y capacidad del lanzador).

**Equipo:** 
- Gonzales Herrera, Emanuel Presley
- Bejarano Gutierrez, William Gonzalo
- Chambi Alcaraz, Bryan Will
- Aguilar Mondragon, Justin Boris
- Arista Vigo, Gian Piero.

**Competencia:** 14 y 15 de noviembre de 2026.


## 1. Descripción

Juego donde el jugador diseña, gestiona y simula una misión espacial completa con recursos limitados. Lo que más premia: retroalimentación que explique POR QUÉ la misión falla o tiene éxito, un puntaje y varios caminos válidos.
Mínimo viable: 2 misiones modelo (p. ej. orbitar la Luna y aterrizar en Marte) y 4–5 decisiones de diseño, con explicación clara del resultado.

Misiones disponibles: **[COMPLETAR]** (misiones modelo definidas por Justin, por ejemplo orbitar la Luna y aterrizar en Marte).

## 2. Cómo jugar

**[COMPLETAR]** Flujo del juego (decidir, simular, ver el resultado y aprender) y descripción de las 5 pantallas: inicio, objetivo, diseño de la nave, lanzador y resultados.

## 3. Cómo ejecutar

Requisitos: Python 3 y las bibliotecas de `requirements.txt` (entre ellas Streamlit).

```bash
pip install -r requirements.txt
streamlit run app.py
```

Estructura prevista del repositorio (ajustar si cambia):

```
datos/              archivos JSON con los datos reales
  lanzadores.json
  misiones.json
  destinos.json
fisica.py           fórmulas físicas (Emanuel)
juego.py            estado, fases, eventos y puntaje (Jhair)
app.py              interfaz en Streamlit (Gonzalo)
requirements.txt
README.md
```

El juego funciona sin conexión: todos los datos están en `datos/`.

---

## 4. Datos

Todos los datos se guardan en `datos/` como JSON (UTF-8). Cada dato numérico lleva su propia fuente. Los costos y capacidades son **valores de referencia para el juego**, no especificaciones contractuales.

### 4.1 Convenciones

| Convención | Detalle |
|---|---|
| Unidades | Van en el nombre de la columna: `_kg`, `_m_s`, `_ua`, `_km`, `_dias`, `_musd` (millones de dólares). |
| Decimales | Punto decimal (`7.5`, no `7,5`). |
| `null` | Significa **dato no disponible o no publicado**. No significa "cero" ni "no puede". El código debe tratarlo como "este lanzador no tiene dato para ese destino" y no usarlo en cálculos. |
| Nombres de destino | Se escriben igual en todos los archivos (por ejemplo, siempre `"Marte"`). |
| Fuente por dato | Cada cifra tiene su columna `fuente_*`. Si el valor es `null`, su fuente también es `null`. |
| Costos | No están ajustados por inflación y corresponden a años distintos. |

### 4.2 `lanzadores.json`

Columnas: `nombre`, `capacidad_leo_kg`, `capacidad_luna_kg`, `capacidad_marte_kg`, `costo_musd`, `fuente_leo`, `fuente_luna`, `fuente_marte`, `fuente_costo`.

Lanzadores incluidos: Electron, Falcon 9, Falcon Heavy, Atlas V 551 y SLS Block 1.

| Lanzador | LEO (kg) | Luna (kg) | Marte (kg) | Costo (M USD) |
|---|---|---|---|---|
| Electron | 300 | 30 | null | 7.5 |
| Falcon 9 | 22 800 | null | 4 020 | 67 |
| Falcon Heavy | 63 800 | 15 460 | 16 800 | 97 |
| Atlas V 551 | 18 850 | null | null | 153 |
| SLS Block 1 | 95 000 | 27 000 | null | 2 200 |

### 4.3 Qué referencia toma cada lanzador

**Las cifras no son comparables de forma directa**, porque cada fabricante las publica bajo condiciones distintas. Esta tabla indica qué significa cada valor.

| Lanzador | Referencia de LEO | Referencia de Luna | Referencia de Marte | Referencia de costo |
|---|---|---|---|---|
| **Electron** | Órbita baja de unos 500 km. | 30 kg a órbita lunar con la plataforma Photon, según un anuncio de 2019. Es una capacidad anunciada, no un vuelo demostrado con esa masa. | Sin dato (`null`). | Precio de lista aproximado, estimación de terceros. |
| **Falcon 9** | Capacidad máxima con **vehículo desechable** (sin recuperar el cohete). Con aterrizaje en barcaza baja a unos 15 600 kg. | Sin dato (`null`). SpaceX no publica una cifra a la Luna. | Capacidad máxima con vehículo desechable. | Precio publicado aproximado; varía según la misión y el año. |
| **Falcon Heavy** | Capacidad máxima con **vehículo desechable**. | "Más de" 15 460 kg a inyección translunar, con vehículo desechable. Con los tres propulsores recuperados baja a unos 8 000 kg. Fuente no oficial. | Capacidad máxima con vehículo desechable. | Precio publicado aproximado. |
| **Atlas V 551** | "LEO-Reference" de ULA: órbita circular de 200 km con inclinación de 28,7°, configuración 551. | Sin dato (`null`). | Sin dato (`null`). Los estudios de NASA dan entre 4 925 y 5 150 kg según el año de lanzamiento, pero no hay una cifra de ULA con un C3 definido. | Estimación de terceros (sitios de seguimiento de lanzamientos). ULA no publica un precio. |
| **SLS Block 1** | 95 t a LEO, cifra de NASA. | "Más de" 27 t a inyección translunar, en la **configuración tripulada con Orion**. | Sin dato (`null`). NASA no publica una cifra para el Block 1. | Solo el cohete (producción), según el Inspector General de NASA. Con Orion y sistemas de tierra, el lanzamiento sube a unos 4 100 M USD. |

Consecuencias para el juego:

- Una misma masa puede "caber" en un lanzador según cómo se mida. Tratar las capacidades como **máximos teóricos**, no como garantías.
- Un cohete con recuperación (reutilizable) lleva menos carga que las cifras de esta tabla. Si el juego quiere ser más realista, se puede aplicar un factor de reducción, que el equipo debe acordar y documentar.
- Los costos de Atlas V y Electron son estimaciones y no contratos reales. El costo de SLS no incluye la nave.
- El SLS no se vende comercialmente: está en el juego como lanzador de referencia para misiones de gran masa.

### 4.4 `destinos.json`

Columnas: `destino`, `delta_v_m_s`, `distancia_ua`, `fuente`.
Destinos: LEO, órbita lunar, superficie lunar y Marte (los valores los aporta Emanuel con su fuente).

**[COMPLETAR]** Tabla con los valores finales.

### 4.5 `misiones.json`

Columnas: `nombre`, `destino`, `masa_kg`, `distancia_km`, `duracion_dias`, `fuente`.
Se incluyen 3 misiones de referencia de NASA.

**[COMPLETAR]** Tabla con las misiones finales.

### 4.6 Cómo leer los datos desde Python

```python
import json

with open("datos/lanzadores.json", encoding="utf-8") as f:
    lanzadores = json.load(f)

for l in lanzadores:
    luna = l["capacidad_luna_kg"]
    if luna is None:
        print(l["nombre"], "- sin dato para la Luna")
    else:
        print(l["nombre"], luna, "kg")
```

---

## 5. Fuentes

Las fuentes están en cada archivo JSON y se resumen aquí. **Fecha de consulta: [COMPLETAR para cada fuente].**

### Lanzadores

| Lanzador | Dato | Fuente |
|---|---|---|
| Electron | LEO | https://rocketlabcorp.com/launch/electron |
| Electron | Luna (30 kg) | SpaceNews, "Rocket Lab to offer lunar missions, ground station services", octubre de 2019 (https://spacenews.com/?p=94601) |
| Electron | Costo | https://www.newspace.im/launchers/rocket-lab |
| Falcon 9 | LEO y Marte | https://www.spacex.com/vehicles/falcon-9 |
| Falcon 9 | Costo | https://keeptrack.space/deep-dive/how-much-does-a-falcon-9-launch-cost (fuente secundaria) |
| Falcon Heavy | LEO y Marte | https://www.spacex.com/vehicles/falcon-heavy |
| Falcon Heavy | Luna | https://www.elonx.net/falcon-heavy-compendium/ (recopilación no oficial) |
| Falcon Heavy | Costo | **[COMPLETAR: reemplazar la fuente actual]** |
| Atlas V 551 | LEO | Cuadernillo de misión de ULA, https://www.ulalaunch.com/docs/default-source/launch-booklets/STPIII_MOB_Final.pdf |
| Atlas V 551 | Costo | https://api.nextspaceflight.com/launches/details/6766 (estimación de terceros) |
| SLS Block 1 | LEO y Luna | Guía de referencia de SLS, NASA |
| SLS Block 1 | Costo | Informe del Inspector General de NASA, https://oig.nasa.gov/docs/IG-22-003.pdf |

### Formato de cita

Adjuntar fuentes:

Cada fuente se registra con: título, entidad, dirección web y fecha de consulta.

---

## 6. Limitaciones y declaración de uso

- Los valores son **de referencia** y pueden diferir de las cifras actuales de los fabricantes.
- Varias fuentes de costo son secundarias o estimaciones de terceros, y están indicadas como tales.
- Los datos en `null` no se rellenaron a propósito, porque no encontramos una fuente que los respalde.
- **Material previo al evento:** antes del 14 de noviembre solo se prepararon datos, tablas, fórmulas y ejercicios de práctica. El juego completo se desarrolló durante el evento. **[COMPLETAR]** Lista de plantillas, bibliotecas y datos usados.

## 7. Licencia

**[COMPLETAR]** Licencia abierta elegida por el equipo (por ejemplo, MIT para el código y CC BY 4.0 para los datos).
