# Métricas de presencia y protagonismo

> **Estado:** borrador conceptual, ajustado a los datos reales (exploración del 20/10/2026; ver `02-datos.md`).

El reto pide una propuesta conceptual de métricas para cuantificar la presencia de las mujeres y su rol protagonista. Separamos dos ideas:

- **Presencia:** cuánto aparecen las mujeres (cantidad).
- **Protagonismo:** qué papel ocupan cuando aparecen (posición y calidad).

## Unidad de análisis

Una **sesión** es una secuencia ordenada de **intervenciones**. Cada una tiene orador/a, rol, género, orden y texto.

**Regla general:** las métricas se calculan sobre las intervenciones de **oradores** (rol distinto de `Chairperson`). La presidencia supone el 57 % de las filas (turnos cortos y procedimentales) y su género solo consta en el 25,5 %, así que se excluye de numeradores y denominadores.

## Métricas de presencia

Valores de referencia sobre ParlaMint-ES 5.0 (2015 a feb. 2023).

| Id | Métrica | Definición | Referencia | Fuente |
|---|---|---|---|---|
| P1 | Proporción de oradoras | Oradoras distintas / oradores distintos | 41,7 % | Metadatos |
| P2 | Proporción de intervenciones | Intervenciones de mujeres / total de oradores | 37,4 % | Metadatos |
| P3 | Proporción de palabras | Palabras de mujeres / total de palabras de oradores | pendiente | Metadatos + texto |
| P4 | Intervenciones por persona | Media de intervenciones por oradora y por orador | 31,7 / 38,0 | Metadatos |

P1 y P2 miden cosas distintas: P1 cuenta personas y P2 cuenta veces que se toma la palabra. Que P1 sea mayor que P2 indica que, de media, cada mujer interviene menos veces que cada hombre.

## Métricas de protagonismo

| Id | Métrica | Definición | Fuente |
|---|---|---|---|
| R1 | Apertura | ¿La primera intervención de un orador en la sesión (o punto del orden del día, si `Agenda` está informado) es de una mujer? | Metadatos |
| R2 | Cierre | ¿La última lo es? | Metadatos |
| R3 | Moderación | **Excluida de las métricas principales.** El género de la presidencia consta solo en el 25,5 % de los turnos y de forma irregular: por año, entre el 10 % y el 35 % de turnos con género, y entre el 14 % y el 84 % de mujeres entre ellos. No es una muestra representativa. Se documenta como dato exploratorio | Metadatos |
| R4 | Intervenciones largas | Proporción de las intervenciones más largas (p. ej. el 25 % superior) que son de mujeres | Texto |
| R5 | Posición temprana | Posición media normalizada (0 a 1) de las intervenciones de mujeres | Metadatos |
| R6 | Reacciones del hemiciclo | Aplausos, murmullos e interrupciones por intervención, según el género de quien habla. Salen de los comentarios del transcriptor entre `[[ ]]` | Texto |

## Métrica de contenido

| Id | Métrica | Definición | Fuente |
|---|---|---|---|
| T1 | Reparto temático | % de mujeres en cada tema respecto de la media (37,4 %) | `Topic` |

Ejemplo observado: Social Welfare 51,6 % frente a International Affairs 26,9 %. Antes de usarla hay que comprobar cómo se asigna `Topic` (parece automático) y qué pasa con los temas con pocos casos.

## Pregunta abierta: dónde entra la IA

Presencia y la mayoría de las métricas de protagonismo salen contando metadatos, con reglas. El reto exige que la IA sea un elemento relevante, así que hay que decidir qué tarea resuelve un modelo sobre el **texto**. Candidatas:

1. **Clasificar los comentarios del transcriptor** (aplauso, murmullo, interrupción, risas) para la métrica R6.
2. **Detectar menciones a mujeres en el discurso** (a quién se nombra o se cita): presencia en el contenido, no solo en quién habla.
3. **Clasificar el tipo de intervención** (pregunta, respuesta, réplica, intervención de fondo).
4. **Tema:** usar `Topic` si su método es fiable, o clasificar con un modelo abierto.

Estimar el género de la presidencia a partir del texto queda descartado: sería una inferencia sobre personas, con riesgo ético y de error, y no es necesaria.

TODO: elegir la tarea (o dos) tras explorar el texto, y definir cómo se valida contra anotación manual.

## Limitaciones a declarar

- Más tiempo de palabra no implica más influencia.
- El género procede de los metadatos del corpus (`M`, `F`, `U`): no recoge otras identidades.
- La moderación no se puede medir de forma representativa.
- Los porcentajes por año y por tema dependen del número de casos; 2016, 2019, 2023 y varios temas tienen pocos.
- Los datos terminan en febrero de 2023.
