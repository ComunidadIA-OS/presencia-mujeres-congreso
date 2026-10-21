# Métricas de presencia y protagonismo

> **Estado:** borrador conceptual, ajustado a los datos reales (exploración del 20 y 21/10/2026; ver `02-datos.md`).

El reto pide una propuesta conceptual de métricas para cuantificar la presencia de las mujeres y su rol protagonista. Separamos dos ideas:

- **Presencia:** cuánto aparecen las mujeres (cantidad).
- **Protagonismo:** qué papel ocupan cuando aparecen (posición y calidad).

## Unidad de análisis

Una **sesión** es una secuencia ordenada de **intervenciones**. Cada una tiene orador/a, rol, género, orden y texto.

**Regla general:** las métricas se calculan sobre las intervenciones de **oradores** (rol distinto de `Chairperson`). La presidencia supone el 57 % de las filas (turnos de unas 26 palabras de media) y su género solo consta en el 25,5 %, así que se excluye de numeradores y denominadores.

## Métricas de presencia

Valores de referencia sobre ParlaMint-ES 5.0 (2015 a feb. 2023).

| Id | Métrica | Definición | Referencia | Fuente |
|---|---|---|---|---|
| P1 | Proporción de oradoras | Oradoras distintas / oradores distintos | 41,7 % | Metadatos |
| P2 | Proporción de intervenciones | Intervenciones de mujeres / total de oradores | 37,4 % | Metadatos |
| P3 | Proporción de palabras | Palabras de mujeres / total de palabras de oradores | 36,1 % | Metadatos + texto |
| P4 | Intervenciones por persona | Media de intervenciones por oradora y por orador | 31,7 / 38,0 | Metadatos |

P1 y P2 miden cosas distintas: P1 cuenta personas y P2 cuenta veces que se toma la palabra. Que P1 sea mayor que P2 indica que, de media, cada mujer interviene menos veces que cada hombre. Que P3 sea menor que P2 indica que sus intervenciones son algo más cortas (548 frente a 580 palabras de media).

## Métricas de protagonismo

| Id | Métrica | Definición | Fuente |
|---|---|---|---|
| R1 | Apertura | ¿La primera intervención de un orador en la sesión (o punto del orden del día, si `Agenda` está informado) es de una mujer? | Metadatos |
| R2 | Cierre | ¿La última lo es? | Metadatos |
| R3 | Moderación | **Excluida de las métricas principales.** El género de la presidencia consta solo en el 25,5 % de los turnos y de forma irregular: por año, entre el 10 % y el 35 % de turnos con género, y entre el 14 % y el 84 % de mujeres entre ellos. No es una muestra representativa. Se documenta como dato exploratorio | Metadatos |
| R4 | Intervenciones largas | Proporción de mujeres entre el 25 % de intervenciones más largas (referencia: 37,4 %, umbral de 836 palabras) | Texto |
| R5 | Posición temprana | Posición media normalizada (0 a 1) de las intervenciones de mujeres | Metadatos |
| R6 | Reacciones del hemiciclo | Aplausos, rumores o protestas y risas por 1.000 palabras, según el género de quien habla y comparando dentro del mismo grupo o estatus. Salen de los comentarios del transcriptor entre `[[ ]]`, clasificados con reglas (cubren cerca del 70 % de las ocurrencias como reacciones; la mayor parte del resto son pausas y restos que no son reacciones) | Texto |

## Métrica de contenido

| Id | Métrica | Definición | Fuente |
|---|---|---|---|
| T1 | Reparto temático | % de mujeres en cada tema respecto de la media (37,4 %) | `Topic` |

Ejemplo observado: Social Welfare 51,6 % frente a International Affairs 26,9 %. Antes de usarla hay que comprobar cómo se asigna `Topic` (parece automático) y qué pasa con los temas con pocos casos.

## Pregunta abierta: dónde entra la IA

Presencia y la mayoría de las métricas de protagonismo salen contando metadatos, y las reacciones (R6) se resuelven bien con reglas: 48 comentarios distintos suman el 82,6 % de las ocurrencias, y lo que queda sin clasificar es sobre todo ruido que no es una reacción. Usar un modelo de lenguaje ahí aportaría poco. El reto exige que la IA sea un elemento relevante, así que hay que elegir una tarea sobre el **texto** que las reglas no resuelvan bien. Candidatas:

1. **Rol de cada intervención en el debate** (defensa de una iniciativa, pregunta o interpelación, respuesta del Gobierno, réplica, fijación de posición, procedimental), usando el anuncio de la presidencia y el comienzo de la intervención. Los metadatos no lo dicen y mide protagonismo de forma directa: quién defiende y quién replica. Se compara con una regla de palabras clave sobre una muestra anotada a mano.
2. **Menciones y tratamiento** (a quién se nombra o se dirige cada orador, y de quién se habla): presencia en el contenido, no solo en quién habla. Una parte se puede resolver con reglas (`señora X`, `señor X`), así que habría que medir qué aporta el modelo.
3. **Tema:** usar `Topic` si su método es fiable, o clasificar con un modelo abierto.

Estimar el género de la presidencia a partir del texto queda descartado: sería una inferencia sobre personas, con riesgo ético y de error, y no es necesaria.

Principio de diseño: reglas como referencia (*baseline*), modelo abierto accesible por una API compatible con OpenAI y sustituible, y evaluación de ambos sobre una muestra anotada a mano. Se clasifica una muestra, no todo el corpus, para usar los recursos de forma responsable.

TODO: elegir la tarea y definir la muestra y las etiquetas.

## Limitaciones a declarar

- Más tiempo de palabra no implica más influencia.
- El género procede de los metadatos del corpus (`M`, `F`, `U`): no recoge otras identidades.
- La moderación no se puede medir de forma representativa.
- Los porcentajes por año y por tema dependen del número de casos; 2016, 2019, 2023 y varios temas tienen pocos.
- Los aplausos dependen del grupo político: sin controlarlo, la comparación por género engaña.
- Los datos terminan en febrero de 2023.
