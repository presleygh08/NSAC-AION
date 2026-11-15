# Especificación de la interfaz — Rocket Run (Pygame, 16 bits)

> Fuente de verdad para construir la interfaz. Escrita por Gonzalo (dueño de `app.py` e `interfaz/`) el 14 nov 2026.
> Complementa a `CONTRATO_API.md` (funciones de `nucleo.py`) y a `docs/reparto-v4.md`. Si algo aquí choca con
> `CONTRATO_API.md`, manda `CONTRATO_API.md` en lo que respecta a funciones y datos; esta especificación manda en
> pantallas, estilo y flujo visual.
> Lo marcado **[PENDIENTE: X]** depende de otra persona: usar el respaldo indicado y no inventar datos.

---

## 0. Reglas que no se rompen

1. **La interfaz no calcula reglas del juego.** Solo llama a funciones de `nucleo.py` según `CONTRATO_API.md`.
   Durante el reparto nunca lee `estado["recursos"]` (trae mínimos y óptimos ocultos); usa `recursos_visibles`.
   Las funciones que aún faltan (sección 9) se agregan directamente en `nucleo.py`, no en la interfaz.
2. **Todo texto visible en inglés**, guardado en `interfaz/textos_en.json` (nunca escrito dentro del código).
   El código, variables y comentarios siguen en español. Las pistas (`estado["pistas"]`) se muestran tal cual
   vienen hasta que Justin las traduzca.
3. **Todo se lee de los datos.** Número de recursos, estaciones, nombres de misión, presupuesto, cohete y destino
   salen de `nucleo.py`. Nada de recursos ni misiones escritos a mano: el equipo va a reasignar recursos por misión.
4. **Archivos que dejan de usarse se renombran con sufijo `_v1`** (ej. `interfaz/juego_stub.py` → `interfaz/juego_stub_v1.py`,
   `interfaz/pantallas.py` → `interfaz/pantallas_v1.py`). No se borran.
5. **Se puede editar cualquier archivo del repo** (incluidos `nucleo.py`, `fisica.py`, `potencia_costo.py` y `datos/`) cuando haga falta para cumplir esta especificación o corregir un error. Condiciones: mantener los nombres de funciones y claves que ya usa `CONTRATO_API.md` (solo añadir), actualizar `CONTRATO_API.md` si se agrega una función, correr las pruebas de `nucleo.py`/`pruebas.py` y `validar_mision` después de tocar la lógica, y decir en el resumen qué archivos de otros integrantes se cambiaron para avisarles.
6. **Unidades:** kg, m/s, W, kbps, days, M USD (mostrar como `$14.5M`).
7. **Prohibido por las reglas del reto:** logos o insignias de la NASA o de misiones; imágenes, video o voz de menores de 18 años.
8. Código simple y comentado, funciones pequeñas. Probar cada etapa con `python3.12 app.py` (el `python3` de Anaconda no tiene pygame).

---

## 1. Estilo visual: 16 bits, indie espacial

- **Resolución lógica 640×360**, dibujada en una `Surface` interna y escalada **×2 a una ventana de 1280×720** con
  `pygame.transform.scale` (vecino más cercano, sin suavizado). Todas las coordenadas del juego son de 640×360.
  `ESCALA` en `config.py` para poder cambiar a ×3.
- **Paleta limitada** (~24–32 colores) definida una sola vez en `config.py`: fondo azul marino espacial, grises
  metálicos para el laboratorio, blanco/cian para texto, y acentos con significado fijo:
  verde = éxito/archivo de pistas · amarillo = advertencia/estrellas · rojo = falla/peligro ·
  azul = interacción (CML 1 y estaciones) · morado = revisión de presupuesto (CML 4).
- **Fuente pixel**: dibujar texto sin antialias (`antialias=False`). Si existe `assets/fuentes/*.ttf` (fuente libre
  OFL/CC0 que agrega Piero, con crédito), usarla; si no, la fuente por defecto de pygame a tamaño pequeño.
- **Ventanas/paneles** con borde pixel (marco de 2 px + sombra de 1 px), esquinas en escalón, estilo cuadro de diálogo de RPG.
- **Sprites dibujados por código** en `interfaz/sprites.py` (superficies pequeñas con `pygame.draw` o matrices de
  píxeles), para no depender de archivos. Cada función de sprite debe poder reemplazarse luego por un PNG de
  `assets/` sin cambiar el resto del código.
- Fondo con estrellas que parpadean suavemente en las pantallas de menú. 60 FPS.

---

## 2. Flujo de pantallas

```
inicio → avatar → misiones → info_mision → laboratorio (CML 1→2→3→4) → simulacion → resultados
                     ↑                                                              │
                     └──────────── "Back to missions" / "Try again" ────────────────┘
```

El estado global de la interfaz es un diccionario en el bucle principal de `app.py`, con al menos:
`pantalla`, `jugador` (nombre + avatar), `progreso` (de `nuevo_progreso()`, se crea una sola vez),
`mision_id`, `estado` (de `iniciar_mision`), `lab` (sub-estado del laboratorio), `resultado`, `revelado`.

---

## 3. Pantallas de menú

### 3.1 Inicio (`inicio`)
- Título **ROCKET RUN** centrado arriba, grande, estilo pixel. Debajo, ilustración: la Tierra, un cohete despegando y estrellas.
- Etiqueta **"Enter your callsign:"** y caja de texto (máx. 12 caracteres: letras, números, espacio; Backspace borra;
  cursor parpadeante). Si queda vacía se usa **"Cadet"**. El NPC usará este nombre en sus diálogos.
- Botón **PLAY** (también Enter). Pasa a `avatar`.

### 3.2 Crea tu avatar (`avatar`)
- Izquierda: avatar **de frente, cuerpo completo**, grande. Derecha: categorías con flechas ◀ ▶ para cambiar cada opción:
  - **Body**: 3 siluetas (Body 1, 2, 3). *No se etiquetan como género*: cualquier ropa, peinado y accesorio sirve con cualquier cuerpo.
  - **Skin tone**: 6 muestras de color, sin nombres.
  - **Hair**: estilo (short, long, curly, afro, braids, buzz, bald) y color (negro, castaño, rubio, pelirrojo, gris, y uno de fantasía).
  - **Eyes**: 3–4 formas + color.
  - **Accessory**: none, glasses, cap, headphones, headscarf, space helmet.
  - **Top**: 4–5 prendas/colores. **Bottom**: pantalón + zapatos, 4–5 opciones.
- Botones **RANDOM** y **CONTINUE**. El avatar se guarda en `jugador["avatar"]` (diccionario de índices).
- Del mismo diccionario sale el **sprite pequeño visto desde arriba** que camina en el laboratorio (mismos colores de piel, pelo, polo y pantalón).
- Inclusión: la diversidad está en las opciones, no en etiquetas. Nada de "male/female".

### 3.3 Elige tu misión (`misiones`)
- Título **"Choose your mission"**. Datos de `cargar_misiones(progreso)`.
- Lista de filas a la **derecha**: nombre (`nombre`, ya en inglés), etiqueta de dificultad con color
  (Easy verde, Normal cian, Hard amarillo, Harder naranja, Insane rojo) y estado:
  `disponible` normal · `completada` con su mejor puntaje · `bloqueada` gris con candado · `proximamente` gris con "Coming soon".
- Panel de **previsualización a la izquierda**: se actualiza al pasar el cursor o hacer clic en una fila.
  Imagen de la misión real (sección 8) + destino y cohete.
- Botón **NEXT** (activo solo si `puede_jugar(progreso, id)`) → `info_mision`. Botón **BACK** → `avatar`.

### 3.4 Ficha de la misión (`info_mision`)
- Izquierda, título con el nombre de la misión y, debajo: **Description**, **Objective**, **Rocket**, **Destination**,
  **Resources to balance** (nombres traducidos de las claves de `recursos_visibles`) y **Budget**.
  **[PENDIENTE: Chambi/Justin]** `parametros_misiones.json` aún no trae descripción ni objetivo en inglés: mientras
  tanto, leerlos de `textos_en.json` → `misiones.<id>.descripcion/objetivo` (textos provisionales cortos) y si no existen mostrar "Coming soon".
- Derecha: imagen de previsualización (la misma de la parrilla, más grande).
- Botón rojo grande **RUN** → crea `estado = iniciar_mision(cargar_parametros(id))` y pasa a `laboratorio`. **BACK** → `misiones`.

---

## 4. Laboratorio (`laboratorio`) — núcleo jugable

### 4.1 Distribución (640×360)
- **Izquierda (~60 %): sala de control vista desde arriba** (top-down), con paredes y suelo de baldosas.
  - **Arriba:** mesa con computadora → punto de interacción **CML 1** (marcador "!" azul).
  - **Derecha:** mesa de control larga → una **estación por recurso** (marcadores "i" azules), tantas como recursos tenga la misión.
  - **Izquierda:** estantes/archivo de registros → **"!" verde** (pistas) y, más tarde, **"!" morado** (revisión de presupuesto).
  - **Abajo:** cuadro de diálogo del **NPC** (retrato del NPC a la derecha del cuadro) con el título del CML en rojo y la instrucción.
- **Derecha (~40 %): ventana al hangar** con el cohete de la misión en su torre de lanzamiento.
- **HUD de presupuesto** siempre visible abajo a la izquierda: `Budget left: $X.XM / $Y.YM` (`presupuesto_restante`),
  en rojo si es negativo.

### 4.2 Movimiento e interacción
- El avatar se mueve con **flechas o WASD**, velocidad constante, con colisión contra paredes y muebles (`pygame.Rect`).
- Al estar cerca (radio ~20 px) de un marcador activo aparece **"[E] Interact"**; con **E** (o clic sobre el marcador) se abre su ventana.
- Con una ventana abierta el avatar no se mueve. **Esc** cierra la ventana (salvo en las que exigen confirmar).
- Los marcadores flotan arriba y abajo (animación de 2 px) para llamar la atención.

### 4.3 Secuencia de fases (sub-estado `lab["fase"]`)

| Fase | NPC (título / texto) | Qué está activo | Al terminar |
|---|---|---|---|
| `cml1` | **Concept Maturity Level 1: Cocktail Napkin** — "Go to the computer and confirm your mission." | Solo el "!" azul de la computadora. El cohete del hangar está **tapado con cortinas**. | Ventana **Mission briefing**: Goal, Destination y Rocket como campos estilo lista desplegable con una sola opción (los datos de la misión), botón **CONFIRM**. Al confirmar: **animación de cortinas abriéndose** y se revela el cohete. |
| `cml2` | **Concept Maturity Level 2: Initial Feasibility** — "Study the mission conditions." | Se abre sola la ventana **Update information**: lista de pistas (`estado["pistas"]`), botón **NEXT**. | Ventana: "Your clues are stored in the archive. Visit the green ! anytime to review them." + **ACCEPT**. Aparece el "!" verde en el archivo (queda activo hasta el final). |
| `cml3` | **Concept Maturity Level 3: Trade Space** — "Visit each station and assign your resources." | Aparecen los "i" azules de cada estación. Archivo verde disponible. | Cuando **todas** las estaciones se confirmaron al menos una vez → `cml4`. |
| `cml4` | **Concept Maturity Level 4: Point Design** — "Go to the archive for the budget review." | Aparece el "!" morado en el archivo. Las estaciones siguen editables. | Ventana **Budget review** (4.5). |

Los textos del NPC pueden incluir el nombre del jugador (ej. "Good job, {nombre}!"). Todos en `textos_en.json`.

### 4.4 Ventana de estación de recurso
- Título: nombre del recurso en inglés + unidad (ej. **Propulsion (delta-v) — m/s**) y una línea que explica qué mide
  (de `textos_en.json`; tabla de nombres en sección 7).
- **Caja de texto numérica**: el jugador escribe la **cantidad del recurso** en su unidad (números y punto decimal).
- Mientras escribe, en vivo: **"Cost: $X.XXM"** y **"Budget left after this: $Y.YYM"** (rojo si queda negativo).
  El costo sale de `cotizar(estado, clave, valor)` (sección 9).
- Botones **CONFIRM** y **CANCEL**. Al confirmar: `repartir(estado, clave, costo)`, se marca la estación como hecha
  (el "i" pasa a ✓ pero sigue editable) y se reproduce la **animación de ensamblaje** de ese recurso en el hangar (4.6).
- Si el texto no es un número válido o es negativo: mensaje en rojo "Enter a valid number" y no se confirma.

### 4.5 Ventana Budget review (CML 4)
- Llama a `revisar(estado)`.
- **Si `ok` es False:** título **BUDGET REVIEW**, mensaje "You have exceeded the budget by $X.XM. Adjust your resources."
  (o el `mensaje` que devuelve `revisar`) + botón **ACCEPT** que cierra y deja moverse libremente para corregir.
- **Si `ok` es True:** "Costs are within the assigned budget." + botón **CONFIRM LAUNCH** → `simulacion`.
  Ojo: con `ok` True el núcleo pasa a la fase de simulación y ya no se puede repartir, así que esta ventana no tiene botón de volver.

### 4.6 Hangar (lado derecho)
- Cohete de la misión en pixel art dentro de la torre. Antes de CML 1 lo cubren **cortinas** que se abren hacia los lados (~1 s).
- **Animación al confirmar cada recurso** (~1,5 s, en el hangar, sin bloquear al jugador):
  - estructura → brazo robótico coloca paneles/vigas en el cohete;
  - propulsión → manguera de combustible llena el tanque (barra que sube);
  - potencia → se despliegan paneles solares;
  - comunicaciones → se monta una antena parabólica;
  - datos → una caja de instrumentos sube con grúa;
  - tiempo → carga de suministros/baterías.
- El cohete muestra visualmente qué partes ya se ensamblaron, sin revelar si alcanzan el mínimo.

---

## 5. Simulación (`simulacion`)

- Antes de animar se llama a `simular(estado)`; el resultado se guarda pero **no se muestra todavía**.
- **Primeros ~5 s idénticos para éxito y falla** (tensión): cuenta regresiva T-3, 2, 1, ignición, humo, despegue y ascenso
  con fondo que pasa de cielo a espacio. El NPC lanza frases de una línea (sección 7.2).
- Luego la animación se **ramifica** según `resultado`:
  - **Éxito** (personalizado por destino): LEO → despliegue del CubeSat/satélite en órbita; órbita de Marte → inserción orbital;
    superficie de Marte → aterrizaje; órbita lunar → órbita alrededor de la Luna.
  - **Falla** (según `resultado["falla"]`): `explota` → el cohete se desarma y explota en el ascenso ·
    `no_llega` → motores se apagan antes de tiempo y la nave cae/no alcanza la órbita ·
    `se_apaga` → la nave llega pero sus luces y paneles se apagan · `incomunicada` → llega pero las ondas de señal se cortan antes de la Tierra ·
    `sin_ciencia` / `fuera_de_tiempo` → la nave queda a la deriva sin cumplir la meta.
- Botón **SKIP** (o Espacio) salta al final. Al terminar → `resultados`.
- **Prioridad:** para Easy, hacer completas la animación común, el éxito en LEO, `explota` y `no_llega`. Las demás pueden ser genéricas al principio.

---

## 6. Resultados (`resultados`)

Se usa `revelar(estado)` y luego `registrar_resultado(progreso, estado)` **una sola vez**.

### 6.1 Si ganó (`exito` True)
- Título **"Mission complete!"** y **5 estrellas** (llenas en amarillo según `estrellas`, sección 9).
- Tabla **Score**: por recurso → Your value, Minimum, Optimal, Points; y una fila **Budget used** (%).
  Puntaje total grande. `mensaje` de `revelar` debajo.
- Si `optimo` es True: sello "Optimal design!".

### 6.2 Si perdió (`exito` False)
- Título en rojo con la falla principal: explota → "The rocket broke apart" · no_llega → "The ship didn't reach its destination" ·
  se_apaga → "The ship ran out of power" · incomunicada → "The ship lost contact with Earth".
- Lista de **recursos bajo el mínimo** (`bajo_minimo`): valor vs mínimo, **% faltante** (sección 9) y una etiqueta
  cualitativa: "Just short" (< 10 %), "Short" (10–30 %), "Far below" (> 30 %). `mensaje` de `revelar` explica el porqué físico.
- Revela también mínimo y óptimo de todos los recursos (es la parte educativa).

### 6.3 Botones (en ambos casos)
**TRY AGAIN** → nueva `iniciar_mision(cargar_parametros(id))` y vuelve al laboratorio (desde `cml1`) ·
**BACK TO MISSIONS** → `misiones` (la parrilla refleja desbloqueos).

---

## 7. Textos (inglés) para `textos_en.json`

### 7.1 Nombres de recursos (claves de los datos → texto)
estructura → Structure (kg) · propulsion → Propulsion (delta-v, m/s) · potencia → Power (W) ·
comunicaciones → Communications (kbps) · datos → Science data (points) · tiempo → Time (days).
Destinos: LEO → Low Earth Orbit · órbita de Marte → Mars orbit · superficie de Marte → Mars surface · órbita lunar → Lunar orbit.

### 7.2 Frases del NPC en la simulación
- Liftoff: "T-3, 2, 1... Ignition! Engines at full power. Let's see if your numbers hold."
- explota: "Structural alert! The vibration was stronger than the ship."
- no_llega: "Engines cut off too early! Not enough delta-v to reach the target."
- se_apaga: "Batteries at zero! We used more energy than we generated."
- incomunicada: "We made it... but our signal can't reach Earth!"
- sin_ciencia / fuera_de_tiempo: "The ship survived, but without enough instruments or time we missed the goal."
- Éxito: "Mission accomplished! You think like a real mission designer."

### 7.3 NPC fuera del laboratorio (etapa final, opcional)
Parrilla: "Here are the station's missions. Start with Easy to master the budget split. Each mission you complete unlocks a new real engineering challenge."
Las notificaciones del asistente se detallarán después: dejar una función `mostrar_notificacion(texto, expresion)` y un cuadro reutilizable.

---

## 8. Imágenes de previsualización de misiones

- Fotos reales de NASA (dominio público en general) que **elige Piero**, guardadas como `assets/misiones/<id>.png`
  (ej. `easy_cubesat.png`), con su fuente en `assets/CREDITOS.md`. **Sin logos ni insignias de misión.**
- El código las **pixela al cargarlas**: reducir a ~120×80, cuantizar a la paleta del juego y volver a escalar sin suavizado.
- Si el archivo no existe: dibujar un placeholder en pixel art (planeta/órbita según destino) con el nombre de la misión.

---

## 9. Lo que falta en `nucleo.py` (agregarlo ahí; detalle en `docs/pedidos-emanuel.md`)

| Necesidad | Función a agregar | Si no da tiempo |
|---|---|---|
| Costo de una cantidad de recurso (estación) | `cotizar(estado, clave, valor)` → M USD | Imprescindible: implementarla en `nucleo.py` usando `costo_de` |
| Estrellas 0–5 con bonus por ahorro | `estrellas(estado)` y bonus de ahorro dentro de `puntaje`/`revelar` | Umbrales en `config.py`: 0 si falló; 1 ≥ 1; 2 ≥ 40; 3 ≥ 60; 4 ≥ 80; 5 si `optimo` |
| % faltante por recurso fallido | campo `faltante_pct` en cada fila de `revelar` | Mostrar solo valor vs mínimo sin porcentaje |
| Descripción y objetivo por misión | campos en `parametros_misiones.json` (Chambi/Justin) | `textos_en.json` → `misiones.<id>` |

Implementar estas funciones en `nucleo.py` siguiendo `docs/pedidos-emanuel.md` (con pruebas), actualizar `CONTRATO_API.md` y avisar a Emanuel qué se agregó.

---

## 10. Organización de archivos sugerida

```
app.py                     bucle principal, estado global, escalado 640x360 → ventana
interfaz/config.py         resolución, escala, paleta, teclas, rutas, umbrales provisionales
interfaz/textos_en.json    todos los textos visibles
interfaz/estilo.py         fuentes pixel, paneles con borde pixel, texto con sombra
interfaz/componentes.py    Boton, CajaTexto, Ventana (modal), Selector ◀ ▶, HUD de presupuesto
interfaz/sprites.py        avatar (frente y top-down), muebles, marcadores, NPC, cohete, cortinas, animaciones del hangar
interfaz/pantalla_inicio.py, pantalla_avatar.py, pantalla_misiones.py, pantalla_info.py
interfaz/laboratorio.py    sala, movimiento, colisiones, fases CML, ventanas
interfaz/simulacion.py     animación común + ramas
interfaz/resultados.py     pantallas de victoria y derrota
assets/misiones/, assets/fuentes/, assets/CREDITOS.md
```

## 11. Prioridad (quedan ~24 h)
1. Easy jugable de punta a punta con todas las pantallas (aunque con formas simples).
2. Estilo 16 bits y laboratorio con movimiento y fases CML.
3. Hangar (cortinas + ensamblaje), simulación de Easy y resultados.
4. Pulido, otras misiones con animaciones genéricas, notificaciones del asistente.
