# Versión 3 — cambios decididos (15 nov 2026)

> Fuente de verdad para la v3. Manda sobre `docs/v2-cambios.md` y `docs/especificacion-interfaz.md` donde choquen.
> Base de datos verificada: `docs/auditoria-datos.md`. Contenido en inglés: `interfaz/guia_misiones_en.json`
> (ya actualizado con las pistas nuevas). Las pistas de `parametros_misiones.json` ya están en inglés en `pistas`
> y en español en `pistas_es`.
> Reglas de CLAUDE.md: se puede editar todo; solo añadir nombres; actualizar `CONTRATO_API.md`; correr las pruebas
> de `nucleo.py`, la validación fina y actualizar `docs/evidencia_validacion_misiones.md`; listar al final los
> archivos de otros integrantes que se cambiaron.

## Orden de trabajo
1. **Datos (A)** → 2. **TRY AGAIN desde CML 4 (B)** → 3. **Gorro navideño (F)** → 4. **Revisión del inglés (D)** →
5. **Selector de idioma inglés/español (E)** → 6. **Textos dentro de sus cuadros en ambos idiomas (C)** → 7. **Fuentes (G)**.

## A. Corregir los datos que contradicen fuentes oficiales (`datos/parametros_misiones.json`)
Regla de costos: los costos son estimaciones del juego. Al cambiar mínimo/óptimo, **ajusta el costo por unidad (o por m²)
para que el costo del óptimo quede aproximadamente igual que antes**, así los presupuestos no se disparan. Marca en la
`nota` qué es dato real (con fuente) y qué es estimado. Luego recalcula presupuestos con `presupuesto_sugerido` (regla D2 de la v2) y valida.

| Misión | Recurso | Antes | Ahora | Fuente del dato real |
|---|---|---|---|---|
| hard_mro_marte | potencia | 550 / 800 W | mín **850 W** (estimado), ópt **1000 W** | NSSDCA vía Planetary Society: los paneles de MRO producen 1000 W en Marte |
| hard_mro_marte | comunicaciones | 30 / 230 kbps | unidad **Mbps**: mín **1.0** (estimado), ópt **6.0** | MRO: tasa máxima 6 Mbps (NSSDCA vía Planetary Society) |
| harder_perseverance | potencia | solar 600 / 850 W | **fuente nuclear (MMRTG), cálculo lineal**: mín **100 W** (estimado), ópt **110 W**. Quitar `eficiencia_panel` y `musd_por_m2_panel` de esta misión para que `preparar_parametros` no le ponga física solar; usar `musd_por_unidad` | NASA/JPL: MMRTG de ~110 W |
| insane_artemis1 | potencia | 800 / 1100 W | mín **9000 W** (estimado), ópt **11200 W** | Airbus/ESA: el módulo de servicio europeo genera ~11.2 kW |

- La interfaz muestra la unidad que venga en el JSON (kbps → Mbps en Hard). Revisa `textos_en.json` / unidades.
- Las animaciones de falla `se_apaga` en Harder deben tener sentido sin paneles solares (por ejemplo, baterías que se agotan).
- Las fichas de Hard y Harder ya aclaran que los cohetes reales fueron Atlas V 401 y Atlas V 541: mantenerlo.

## B. TRY AGAIN continúa desde CML 4
- Después de una falla (o de un éxito), **TRY AGAIN** vuelve al laboratorio **directamente en la fase CML 4**: puertas del hangar abiertas,
  cohete ensamblado, todas las estaciones confirmadas (✓) con las cantidades anteriores ya escritas, archivo verde disponible,
  marcador morado de revisión activo y AION con el texto de CML 4. No repetir CML 1–3 ni la pantalla didáctica.
- Internamente: `iniciar_mision(cargar_parametros(id))` + volver a aplicar el reparto anterior con `cotizar`/`repartir`.
- El jugador aparece cerca de la mesa de control para editar los recursos que fallaron.
- **Restart mission** (menú de pausa) sigue empezando desde CML 1.

## C. Ningún texto fuera de su cuadro
- Revisa todas las pantallas y ventanas, en inglés y en español (el español es ~20 % más largo).
- Ajuste por: salto de línea por palabras, márgenes internos, reubicación y tamaño de los cuadros.
  **Mantén la fuente pixel actual** y prioriza la estética.
- Agrega una comprobación automática (modo de prueba) que recorra las pantallas y avise si un texto supera su rectángulo.
- Solo si es rigurosamente necesario, aumenta la resolución lógica (por ejemplo 640×360 → 768×432, conservando 16:9 y el escalado entero) y explica por qué.

## D. Inglés riguroso con terminología de NASA
Revisa todo texto visible (`textos_en.json`, `guia_misiones_en.json`, `datos/mensajes.json`, pistas). Términos: low Earth orbit (LEO),
sun-synchronous orbit, delta-v, trans-lunar injection, Mars orbit insertion, entry, descent and landing (EDL), high-gain antenna, X-band,
solar array, Multi-Mission Radioisotope Thermoelectric Generator (MMRTG), Concept Maturity Level (CML), payload, dry mass, launch vehicle.
Ortografía y mayúsculas consistentes (sentence case en botones), sin mezclar español.

## E. Selector de idioma (inglés por defecto, español)
- Archivos: `interfaz/textos_es.json` (espejo exacto de `textos_en.json`), `interfaz/guia_misiones_es.json` (espejo de la guía),
  `datos/mensajes_es.json` (espejo de `mensajes.json`; en `nucleo.py` añadir un parámetro de idioma opcional que no rompa lo existente).
  Pistas: `pistas` (en) y `pistas_es` (es).
- Traducción al español neutro latinoamericano, técnica y fiel (delta-v se mantiene; "órbita terrestre baja (LEO)", "inyección translunar", etc.).
- **Dónde:** pantalla de inicio (botones EN | ES visibles) y menú de pausa (opción "Language / Idioma"). Cambia al instante, sin reiniciar la misión.
  Inglés al abrir el juego.
- Si falta una clave en español, usar la inglesa (nunca mostrar la clave cruda).

## F. Gorro navideño
Nueva opción de accesorio **"Santa hat"** (rojo con borde y pompón blancos), en el sprite frontal y en el sprite visto desde arriba.

## G. Fuentes y estimaciones
En la pantalla de créditos/fuentes: lista de fuentes (`guia_misiones_en.json` → `fuentes`) y la nota `creditos_finales.estimaciones`.
