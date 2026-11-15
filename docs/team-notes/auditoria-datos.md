# Auditoría de datos — Star Forge (15 nov 2026)

Revisión de `datos/parametros_misiones.json`, `datos/lanzadores.json`, `datos/destinos.json` e `interfaz/guia_misiones_en.json`
contra fuentes oficiales (NASA primero; ESA/DLR y fabricantes cuando NASA no publica el dato).
Leyenda: ✅ verificado · ⚠️ no sustentado (estimación o fuente no oficial) · ❌ contradice la fuente oficial.

## Física y destinos
| Dato en el juego | Estado | Fuente / comentario |
|---|---|---|
| Irradiancia solar en la Tierra 1361 W/m² | ✅ | NASA NSSDC Mars Fact Sheet (valor de la Tierra en la tabla comparativa) |
| Marte a 1.524 UA del Sol | ✅ | NASA NSSDC Mars Fact Sheet: 1.52366 UA |
| Irradiancia en Marte 586 W/m² | ✅ | NASA NSSDC Mars Fact Sheet: 586.2 W/m² |
| Delta-v de destinos (9400 / 13400 / 14400 / 18500 m/s) | ⚠️ | `destinos.json` cita "NASA delta-v map": no existe un mapa oficial de NASA con esos números (son de mapas de la comunidad). Valores plausibles, pero hay que presentarlos como aproximados. |

## Lanzadores
| Dato | Estado | Fuente / comentario |
|---|---|---|
| Electron: 300 kg a LEO | ✅ | Rocket Lab (anuncio oficial, 2020) |
| Electron: costo 7.5 M USD | ⚠️ | Precio de lista citado por terceros; Rocket Lab no publica tarifa |
| Falcon 9: 22,800 kg a LEO; 4,020 kg a Marte | ✅ | Cifras anunciadas por SpaceX |
| Falcon Heavy: 63,800 kg a LEO; 16,800 kg a Marte | ✅ | spacex.com/vehicles/falcon-heavy |
| Falcon Heavy: 15,460 kg a la Luna | ⚠️ | No aparece en la página de SpaceX |
| Costos Falcon 9 (67) y Falcon Heavy (97) | ⚠️ | Precios históricos de SpaceX; no verificados hoy |
| SLS Block 1: >27 t a la Luna; >95 t a LEO | ✅ | NASA (fact sheet y artículo "The Great Escape") |
| SLS: costo 2,200 M USD | ⚠️ | Estimación de la Oficina del Inspector General de NASA; no verificada hoy |

## Misiones
| Misión / dato | Estado | Fuente / comentario |
|---|---|---|
| Easy – masa seca CubeSat 20 kg, fracción estructural 25–30 %, Isp 220 s | ⚠️ | Valores de referencia razonables (NASA SmallSat / SoA), no de una misión concreta |
| Normal – inspirada en Pandora (Falcon 9, 11 ene 2026) | ✅ | NASA Small Satellite blog, ene 2026 |
| Normal – masa seca 140 kg y resto de valores | ⚠️ | Genéricos de "smallsat"; no son de Pandora → el texto dice "inspired by" |
| Hard – masa seca MRO ≈1030 kg | ✅ | NASA/JPL: subsistemas e instrumentos < 1,031 kg; 1,149 kg de propelente |
| Hard – cohete Falcon Heavy | ❌ | MRO voló en Atlas V 401 (el juego ya lo aclara en la ficha) |
| Hard – potencia mín 550 / ópt 800 W | ✅ corregido (v3) | Ahora 850 (estimado) / **1000 W**: los paneles de MRO producen ~1000 W en Marte (NSSDCA vía Planetary Society) |
| Hard – comunicaciones 30–230 kbps | ✅ corregido (v3) | Ahora en Mbps: 1.0 (estimado) / **6.0 Mbps**, la tasa máxima de MRO (30–230 kbps era Mars Express, ESA) |
| Hard – estructura 375–475 kg | ⚠️ | Estimación sin fuente |
| Harder – cohete Falcon Heavy | ❌ | Perseverance voló en Atlas V 541 (el juego ya lo aclara) |
| Harder – potencia solar 600–850 W | ✅ corregido (v3) | Ahora MMRTG con cálculo lineal: 100 (estimado) / **110 W** + baterías (NASA/JPL) |
| Harder – masa seca 1900 kg | ⚠️ | El rover pesa 1,025 kg (NASA/JPL); 1900 kg no tiene fuente |
| Harder – instrumentos 59 kg (7 instrumentos) | ⚠️/✅ | "7 instrumentos" ✅ NASA; "59 kg" solo en fuente secundaria (rocketstem.org) |
| Insane – duración 25.5 días | ✅ | NASA (comunicado del amerizaje) |
| Insane – instrumentos 98 kg (MARE: 36 + 62 kg) | ✅ | DLR (agencia espacial alemana) |
| Insane – potencia 800–1100 W | ✅ corregido (v3) | Ahora 9000 (estimado) / **11 200 W**: el módulo de servicio europeo de Orion genera ~11.2 kW (Airbus/ESA) |
| Insane – masa seca Orion 10,300 kg | ⚠️ | Sin fuente oficial verificada |
| Insane – delta-v 4000 m/s de la "nave" | ⚠️ | Simplificación: en la realidad la inyección lunar la hace la etapa ICPS del SLS, no Orion |
| Todos los costos "M USD por unidad" | ⚠️ | Estimaciones del equipo para el juego; no hay tarifas oficiales. En la v3 se ajustaron para que el costo del óptimo no cambie (ver `docs/evidencia_validacion_misiones.md`) |
| Margen de diseño 20 % | ✅ | ESA, Margin philosophy for science assessment studies |
