# Versión 2 — cambios decididos (15 nov 2026)

> Fuente de verdad para la v2. **Manda sobre `docs/especificacion-interfaz.md` donde choquen.**
> Origen: documento ERRORES_Y_SUGERENCIAS del equipo + decisiones de Gonzalo.
> Contenido en inglés para pantallas nuevas: `interfaz/guia_misiones_en.json` (no inventar textos ni cifras: usar ese archivo).
> Se puede editar cualquier archivo (incluidos `nucleo.py` y `datos/`) con las reglas de CLAUDE.md:
> solo añadir nombres, actualizar `CONTRATO_API.md`, correr pruebas y validación, y listar al final los archivos de otros integrantes que se cambiaron.

## Decisiones de diseño

| # | Tema | Decisión |
|---|---|---|
| D1 | Presupuesto durante el reparto | El HUD muestra `Budget: $X.XM` (fijo) + un **indicador de color sin cifras**: verde si el total cabe en el presupuesto, rojo si se pasó (usa solo el signo de `presupuesto_restante`). Nunca mostrar total gastado, restante ni exceso. La estación sigue mostrando el costo de ESE recurso. |
| D2 | Presupuestos | **Subir el presupuesto** de cada misión para que los óptimos sí quepan y las 5 estrellas sean alcanzables: `presupuesto_musd` = el menor valor "redondo" ≥ **1.05 × Σ costo(óptimos)** que siga funcionando con `paso_dinero`. Agregar `presupuesto_sugerido(parametros)` en `nucleo.py`, actualizar `datos/parametros_misiones.json`, volver a correr la validación fina y actualizar `docs/evidencia_validacion_misiones.md`. El reto sigue: gastar de más en un recurso deja menos para otro, y el bonus premia ahorrar. |
| D3 | Qué se revela al final | **Nunca cifras exactas de mínimo ni óptimo**, salvo con **5 estrellas**. Por recurso: barra con zonas (rojo = bajo el mínimo, amarillo = aceptable, verde = cerca del óptimo ±10 %, naranja = de más) y la marca del valor del jugador, más una pista: "Needs much more", "Needs a bit more", "Close to optimal", "More than needed". Agregar a cada fila de `revelar` los campos `zona` (`bajo_minimo`/`aceptable`/`optimo`/`exceso`) y `pista`. En derrota, quitar el "% short" numérico (revela el mínimo): solo la etiqueta cualitativa. Con 5 estrellas se muestra la tabla completa con cifras. |
| D4 | Ayuda didáctica | Rangos de referencia amplios (nunca el mínimo exacto): ya escritos en `guia_misiones_en.json` → `misiones.<id>.pistas_referencia`. |
| D5 | Guía | El "director" se reemplaza por **AION**, un robot pequeño y tierno (pixel art, ojos grandes, antena, 3–4 expresiones: neutral, feliz, alerta, celebrando). AION da los diálogos CML, la pantalla didáctica y un **menú de preguntas predefinidas** (`aion_faq`): en el laboratorio, hablar con AION (tecla H o acercarse a él) abre la lista; elegir una muestra la respuesta. Sin IA externa. |
| D6 | Nombre del juego | **STAR FORGE** en todas partes (título, ventana, textos, README). |
| D7 | Simulación | **Nunca se puede saltar.** Animaciones más largas (parte común ~6 s; total 12–15 s). |
| D8 | Recurso "datos" | **Ya cambiado en `datos/parametros_misiones.json`** (Gonzalo/Claude): ahora es **Science instruments (kg)**, masa de instrumentos científicos. Harder: mín 47, ópt 59 kg (carga real de Perseverance: 7 instrumentos, 59 kg). Insane: mín 80, ópt 98 kg (experimento MARE real de Artemis I). La clave `datos` y la falla `sin_ciencia` no cambian. La interfaz debe mostrar "Science instruments (kg)" (ver `guia_misiones_en.json`). Recalcular presupuestos (D2) con estos valores. |
| D9 | Recursos por nivel | Evaluado: la distribución actual es acumulativa y cada recurso nuevo responde al reto real de su misión (Easy 2 → Insane 6). **Se mantiene.** |
| D10 | Misión Normal | Basada en **NASA Pandora** (smallsat en Falcon 9, 11 ene 2026). Nombres, "inspirada en", descripción, objetivo y dato del cohete de las 5 misiones: `guia_misiones_en.json` → `misiones`. Actualizar también `nombre` en `parametros_misiones.json`. |
| D11 | Sonido | Generado **por código** (pygame.sndarray / ondas sintetizadas, sin archivos con licencia): pitidos de cuenta regresiva T-3, 2, 1, rugido de ignición, sonido de éxito y de falla. Tecla **M** silencia. Si el sistema no tiene audio, el juego sigue sin sonido (no debe fallar). |
| D12 | Nombres de recursos | Usar `guia_misiones_en.json` → `recursos` (ej. Time pasa a **Endurance**). Cada recurso con `que_es` y `por_que_importa`. |

## Prioridad 1 (hacer primero, en este orden)
1. **D3** ocultar cifras en resultados + campos `zona`/`pista` en `revelar`.
2. **TRY AGAIN conserva el reparto**: al reintentar, cada estación viene con la cantidad que el jugador escribió antes (se vuelve a repartir con `cotizar` + `repartir` en el estado nuevo).
3. **Pantalla didáctica** entre la ficha (RUN) y el laboratorio: AION, "inspirada en", dato del cohete, y por recurso de la misión: nombre, unidad, qué es, por qué importa y la referencia. Botón "LET'S DESIGN" / Enter.
4. **Menú de pausa con Esc** (si no hay ventana abierta): Resume, Restart mission (desde CML 1, conservando nada), Back to missions, Main menu. En ventanas abiertas, Esc sigue cerrándolas.
5. **Enter confirma** el botón principal de cada pantalla y ventana (PLAY, CONTINUE, NEXT, RUN, CONFIRM, ACCEPT, CONFIRM LAUNCH, TRY AGAIN). E sigue siendo interactuar.
6. **Mission briefing como texto informativo** (sin flechas de lista desplegable) + CONFIRM.
7. Título **"BUDGET REVIEW: <nombre de la misión>"**.
8. **D1** indicador de color en el HUD.
9. **D2** presupuestos nuevos + validación.
10. **Paneles solares y antenas plegados** en el lanzamiento y en el hangar; se despliegan solo al llegar a órbita en la simulación (Falcon 9 y demás).
11. **D6** Star Forge, **D10** nombres y descripciones, **D12** nombres de recursos.
12. **D7** sin skip.
13. **Pantalla final de créditos** (`creditos_finales`) al completar Insane, y accesible desde el menú principal.

## Prioridad 2 (lo que más luce en el video)
14. **D11** sonido.
15. **Trayectoria con giro por gravedad** (el cohete se inclina y curva, no sube recto), luego **órbita punteada**; el final muestra el objetivo en su lugar: satélite liberado en su órbita alrededor de la Tierra, inserción en órbita de Marte, aterrizaje del rover, órbita alrededor de la Luna.
16. **Tierra con continentes** reconocibles en pixel art (no círculos verdes).
17. **Puertas de hangar metálicas** (franjas de advertencia, se abren deslizándose) en lugar del telón rojo.
18. **AION** como sprite y retrato con expresiones + menú de preguntas (D5).
19. **Sala de control** más real: consolas con pantallas que parpadean, gráficas, reloj de misión, mapa del mundo en una pantalla grande. Sin logos de NASA.

## Futuro (no hacer hoy; va en la página como "next steps")
Rediseño de recursos con más datos reales por misión, modo de hasta 4 jugadores.
