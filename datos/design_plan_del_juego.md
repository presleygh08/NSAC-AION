# Design Plan — Space Mission Design Game

## 1. Inicio y Selección
* **Selección de avatar:** El jugador abre el juego y escoge un avatar a través de un menú de selección personalizable.
* **Parrilla de misiones:** Se muestra una cuadrícula de misiones basadas en misiones espaciales reales.
* **Niveles de dificultad:** Las misiones están etiquetadas por dificultad (`Easy`, `Normal`, `Hard`, `Harder`, `Insane`). A mayor dificultad, mayor cantidad de recursos y variables simultáneas que optimizar.

## 2. Objetivos de la Misión
* **Briefing inicial:** Se presenta la meta de la misión, el destino (`LEO`, `Luna`, `Marte`) y el cohete base con su capacidad de carga y costos reales.
* **Configuración de variables:** Dependiendo de la misión y del nivel de dificultad elegido, se establecen parámetros iniciales y restricciones específicas.

## 3. Gameplay: Base de Operaciones y Control
* **Rol del avatar:** El avatar es el encargado de gestionar toda la base de operaciones, compuesta por múltiples salas conectadas y un puente de acceso hacia la nave (cohete).
* **Desplazamiento y paneles:** Para medir y controlar los distintos parámetros de la misión, el jugador debe desplazar al avatar entre los diferentes ambientes de la base para manipular el panel correspondiente.
* **Eventos aleatorios en el trayecto:** Mientras el avatar se mueve por la base, pueden ocurrir problemáticas imprevistas que debe resolver antes del lanzamiento (por ejemplo: una fuga de propelente, un pequeño incendio en algún pasadizo, etc.).

## 4. Parámetros a Controlar y Optimización
* **Variables del sistema:** El jugador debe calibrar y controlar parámetros clave como:
  * Masa
  * Potencia
  * Presupuesto
  * Estructura
  * $\Delta v$ (Delta-v)
  * Comunicaciones
  * Datos
  * Tiempo
* **Rangos óptimos ocultos:** Existen valores mínimos y máximos óptimos que no se muestran explícitamente al jugador; para obtener el mayor puntaje posible, el jugador debe acercarse a esos valores ideales mediante criterio de ingeniería.

## 5. Lanzamiento y Evaluación
* **Simulación:** Una vez controladas y estabilizadas todas las variables, se procede al lanzamiento del cohete mediante una animación de simulación.
* **Puntaje final:** Al concluir la simulación, se evalúa qué tan cerca estuvo el diseño de los valores óptimos y se muestra una animación con la puntuación final.