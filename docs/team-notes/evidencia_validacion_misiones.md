# Evidencia de Validity: las 5 misiones tienen solución

Fecha: 2026-11-15 (actualizada para la **v3**, punto A) · Datos: `datos/parametros_misiones.json` con la potencia y las
comunicaciones corregidas según fuentes oficiales (ver `docs/auditoria-datos.md`) · Complementa a `evidencia_validacion_easy.md`.

## Cómo se reproduce
```bash
python3 nucleo.py --validar-fino   # tabla de abajo (≈ 3 s)
python3 nucleo.py                  # autopruebas, incluidas las de la v3 (datos corregidos e idioma)
python3 nucleo.py --verificar      # formato de parametros_misiones.json
```
Función: `validar_mision_fina(parametros)` en `nucleo.py`.

## Cambios de datos de la v3 (A)

Regla: el **óptimo** pasa a ser el dato real con fuente; el **mínimo** es una estimación del equipo; el costo por
unidad (o por m² de panel) se ajustó para que el costo del óptimo quede igual que antes, así los presupuestos no cambian.

| Misión | Recurso | Antes (mín / ópt) | v3 (mín / ópt) | Costo unitario | Costo del óptimo antes → ahora | Fuente del óptimo |
|---|---|---|---|---|---|---|
| hard_mro_marte | potencia (solar) | 550 / 800 W | **850 / 1000 W** | `musd_por_m2_panel` 8.21 → 6.57 | 40.03 → 40.04 M | MRO: ~1000 W en Marte (NSSDCA vía Planetary Society) |
| hard_mro_marte | comunicaciones | 30 / 230 kbps | **1.0 / 6.0 Mbps** | 0.1 M/kbps → 3.833 M/Mbps | 23.00 → 23.00 M | MRO: máx. 6 Mbps (NSSDCA vía Planetary Society) |
| harder_perseverance | potencia | solar 600 / 850 W | **MMRTG 100 / 110 W**, cálculo lineal | 0.386 M/W (sin `eficiencia_panel` ni `musd_por_m2_panel`) | 42.50 → 42.46 M | NASA/JPL: MMRTG de ~110 W |
| insane_artemis1 | potencia (solar) | 800 / 1100 W | **9000 / 11200 W** | `musd_por_m2_panel` 20.42 → 2.006 | 55.01 → 55.03 M | Airbus/ESA: módulo de servicio europeo ~11.2 kW |

Harder lleva además `"tipo_potencia": "mmrtg"` (el núcleo lo copia a `estado["tipo_potencia"]`; la interfaz dibuja el
generador nuclear en vez de paneles y, si falta energía, las baterías que se agotan).

Los mínimos subieron respecto del óptimo (antes ~70 %, ahora ~85–90 % en potencia), así que cumplir los mínimos cuesta más:
Σ mínimos de Hard pasa de 97.72 a 105.07 M; Harder de 166.42 a 175.02 M; Insane de 215.49 a 219.70 M.

## Presupuestos (`presupuesto_sugerido`, regla D2 de la v2)

| Misión | Σ óptimos | 1.05 × Σ óptimos | P v2 | **P v3** | Paso − / + |
|---|---|---|---|---|---|
| easy_cubesat | 16.77 | 17.61 | 18 | **18** | 0.5 |
| normal_leo | 67.06 | 70.41 | 71 | **71** | 1 |
| hard_mro_marte | 145.75 | 153.04 | 155 | **155** | 5 |
| harder_perseverance | 225.76 | 237.05 | 240 | **240** | 5 |
| insane_artemis1 | 286.11 | 300.42 | 305 | **305** | 5 |

Como el costo de los óptimos no cambió, `presupuesto_sugerido` devuelve los mismos presupuestos.

## Método
`validar_mision` prueba repartos en escalones del 10 % del presupuesto: es demasiado gruesa. La validación fina:

1. Calcula cuánto cuesta llegar exactamente al **mínimo** de cada recurso (`costo_de`, con la física real
   para propulsión y potencia solar; lineal para el MMRTG).
2. El **sobrante** = presupuesto − Σ costos de los mínimos se reparte entre los recursos en escalones
   pequeños (2 recursos: 200 escalones; 3: 100; 4: 60; 5: 30; 6: 20), probando **todas** las combinaciones,
   incluso las que dejan dinero sin gastar (por el bonus por ahorro).
3. Para cada combinación calcula el puntaje del juego (cercanía al óptimo + bonus por ahorro).
4. El mejor reparto se **vuelve a jugar con las funciones reales** (`iniciar_mision` → `repartir` → `revisar` →
   `simular` → `revelar`) para confirmar que pasa la revisión, completa la misión y da ese puntaje y estrellas.

**Margen razonable:** sobrante ≥ 10 % del presupuesto, Σ mínimos ≤ P ≤ 1.10 × Σ óptimos y 5 estrellas alcanzables
(puntaje ≥ 86 o diseño óptimo).

## Resultados v3 (`python3 nucleo.py --validar-fino`)

| Misión | Recursos | P (M USD) | Σ mínimos | Σ óptimos | Sobrante | Repartos probados | Mejor puntaje | Estrellas | Repartos con 5★ | Margen |
|---|---|---|---|---|---|---|---|---|---|---|
| easy_cubesat | 2 | 18 | 10.99 | 16.77 | 39.0 % | 20 301 | 100 | 5 | 49.0 % | OK |
| normal_leo | 3 | 71 | 43.98 | 67.06 | 38.1 % | 176 851 | 100 | 5 | 32.0 % | OK |
| hard_mro_marte | 4 | 155 | 105.07 | 145.75 | 32.2 % | 635 376 | 100 | 5 | 21.3 % | OK |
| harder_perseverance | 5 | 240 | 175.02 | 225.76 | 27.1 % | 324 632 | 99 | 5 | 12.7 % | OK |
| insane_artemis1 | 6 | 305 | 219.70 | 286.11 | 28.0 % | 230 230 | 97 | 5 | 11.0 % | OK |

"Repartos con 5★" = porcentaje de los repartos que ya completan la misión (todos parten de los mínimos) que
además llegan a 5 estrellas. Con los mínimos más altos, Hard y Harder exigen un reparto algo más cuidado que en la v2.

### Grilla gruesa de `validar_mision` (escalones del 10 %), como referencia
| Misión | Repartos | Completan | Mejor puntaje |
|---|---|---|---|
| easy_cubesat | 66 | 10 (15.2 %) | 93 |
| normal_leo | 286 | 20 (7.0 %) | 92 |
| hard_mro_marte | 1 001 | 1 (0.1 %) | 80 |
| harder_perseverance | 3 003 | 6 (0.2 %) | 95 |
| insane_artemis1 | 8 008 | 0 | — |

Lectura: la mayoría de los repartos "a ojo" no completa la misión, pero con criterio siempre hay solución.
En Insane ningún reparto en escalones del 10 % la completa: hay que repartir con cuidado los 6 recursos.

## Mejores repartos encontrados

| Misión | Dinero por recurso (M USD) | Cantidades que el jugador escribe en cada estación |
|---|---|---|
| easy_cubesat | estructura 8.24 · propulsión 8.25 | 8.2 kg · 399 m/s |
| normal_leo | estructura 17.51 · propulsión 26.79 · potencia 21.83 | 43.8 kg · 644.1 m/s · 545.9 W |
| hard_mro_marte | estructura 22.91 · propulsión 55.11 · potencia 39.86 · comunicaciones 22.97 | 458.2 kg · 5326 m/s · 995.5 W · 6.0 Mbps |
| harder_perseverance | estructura 24.33 · propulsión 91.27 · potencia 40.77 · comunicaciones 23.49 · instrumentos 25.48 | 973.3 kg · 9100 m/s · 105.6 W · 234.9 kbps · 56.6 kg |
| insane_artemis1 | estructura 46.76 · propulsión 80.25 · potencia 52.75 · comunicaciones 26.32 · instrumentos 40.53 · tiempo 24.26 | 4676.5 kg · 4145.2 m/s · 10 736.1 W · 526.5 kbps · 101.3 kg · 24.3 días |

## Conclusión
Las 5 misiones siguen teniendo solución con los datos corregidos de la v3, con sobrante ≥ 27 % y 5 estrellas
alcanzables. Si Chambi cambia mínimos u óptimos, recalcular con `presupuesto_sugerido(cargar_parametros(id))` y repetir
`python3 nucleo.py --validar-fino`.
