# Plan del equipo – Space Mission Design Game (NASA Space Apps 2026)

Fuente: Drive "06. NASA SPACE APPS CHALLENGE" → Plan_NSAC.pdf (v5, 27 oct) y Plan_NASA.pdf (v3, 12 nov). Actualizado el 13 nov 2026.

> Jhair ya no forma parte del equipo. Su parte (estado del juego, fases, puntaje, lectura de datos e integración) pasa a Emanuel. Equipo: 5 integrantes.

## El reto
Juego donde el jugador diseña, gestiona y simula una misión espacial completa con recursos limitados. Lo que más premia: retroalimentación que explique POR QUÉ la misión falla o tiene éxito, un puntaje y varios caminos válidos.
Mínimo viable: 2 misiones modelo (p. ej. orbitar la Luna y aterrizar en Marte) y 4–5 decisiones de diseño, con explicación clara del resultado.

## Roles durante las 48 h
| Integrante | Rol |
|---|---|
| Emanuel | delta_v, masa_propelente, compatibilidad con el lanzador, estado del juego, fases, eventos, puntaje, lectura de datos e integración |
| Gonzalo | Interfaz en Pygame: pantallas conectadas a la lógica de Emanuel; probar las funciones recibidas |
| Chambi | potencia_generada, balance_potencia, costo_total; reglas de falla; validar como ingeniero |
| Justin | Flujo del juego, mensajes.json, pitch y video |
| Piero | lanzadores.json, misiones.json, destinos.json con fuentes; README y entrega |

Nota: los planes escritos dicen Streamlit; la interfaz se hace en Pygame (decisión del 12 nov). El estado del juego es un diccionario en el bucle principal.

## Pantallas
inicio → objetivo → diseño de la nave → lanzador → resultados

## Bucle del juego
Decidir → simular → ver el resultado → aprender.
Fases: objetivo, diseño, lanzador, tránsito, resultado. Estado = diccionario (fase, presupuesto, masa, potencia, resultado). Evento aleatorio (falla con probabilidad p) y puntaje.

## Contrato de datos y funciones (fijado el 12 nov)
Unidades: kg, m/s, W y millones de USD.

Funciones de Emanuel:
- delta_v(isp, m0, mf)
- masa_propelente(delta_v, isp, m_seca)
- evaluar_mision(mision)

Funciones de Chambi:
- potencia_generada(distancia_ua, area_m2, eficiencia)
- balance_potencia(generada_w, consumos)
- costo_total(lanzador, nave, instrumentos)

JSON de Piero (datos/):
- lanzadores.json: nombre, capacidad_leo_kg, capacidad_luna_kg, capacidad_marte_kg, costo_musd, fuente
- misiones.json: nombre, destino, masa_kg, distancia_km, duracion_dias, fuente
- destinos.json: destino, delta_v_m_s, distancia_ua, fuente

Mensajes de Justin (datos/mensajes.json), una clave por resultado:
exito, delta_v_insuficiente, potencia_insuficiente, masa_excede_lanzador, presupuesto_excedido, falla_aleatoria

Regla de oro: cada función recibe y devuelve números o diccionarios, sin print ni lógica de interfaz. Los textos se leen desde archivo.

## Fórmulas
- Δv = Isp·g0·ln(m0/mf), g0 = 9,80665 m/s²
- mp = ms·(e^(Δv/(Isp·g0)) − 1); m0 = ms + mp (se compara con la capacidad del lanzador)
- S = S0/d² (d en UA); P = S·A·η
- C = C_lanzador + C_nave + C_instrumentos

## Cronograma de las 48 h
- Sáb. mañana: integrar física, juego, datos y pantallas. Una misión completa, aunque sea básica.
- Sáb. tarde: segunda misión, dificultad, eventos y mensajes de «por qué falló».
- Dom. mañana: informe de misión, puntaje. Sin funciones nuevas tras el mediodía.
- Dom. tarde: pruebas, README, video y entrega antes de las 11:59 p. m. (hora de Lima).

## Reglas
- Cada función con comentario: qué recibe, qué devuelve y en qué unidades.
- Commit + push al cierre de cada bloque de trabajo.
