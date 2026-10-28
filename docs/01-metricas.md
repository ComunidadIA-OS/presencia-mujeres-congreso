# Métricas de presencia y protagonismo

> **Estado:** 28/10/2026. Definiciones ajustadas a los datos reales (exploración del 20 y 21/10; ver `02-datos.md`) y resultados sobre todo el corpus de presencia (P1–P4), posición en el debate (R1, R2, R5) y rol en el debate (R7, clasificado con IA en las 26.586 intervenciones de diputadas y diputados). La evaluación del clasificador está en `05-evaluacion.md` y `06-acuerdo-y-confirmacion.md`.

El reto pide una propuesta conceptual de métricas para cuantificar la presencia de las mujeres y su rol protagonista. Separamos dos ideas:

- **Presencia:** cuánto aparecen las mujeres (cantidad).
- **Protagonismo:** qué papel ocupan cuando aparecen y en qué momento del debate (posición y calidad).

## Unidad de análisis

Una **sesión** es una secuencia ordenada de **intervenciones**. Cada una tiene orador/a, rol, género, orden y texto.

Cada sesión se divide en **secciones del orden del día** (por ejemplo, «PREGUNTAS» o «PROPOSICIONES NO DE LEY»). La columna `Agenda` de los metadatos está vacía en las 76.369 filas, así que las secciones se toman de los encabezados `<head>` de la versión XML (TEI) del corpus: cada encabezado abre una sección nueva. El XML pone un encabezado por sección, no por cada pregunta o iniciativa. En todo el corpus hay 1.372 secciones en 450 sesiones (unos 3 por sesión y unos 21 turnos de oradores por sección).

**Regla general:** las métricas se calculan sobre las intervenciones de **oradores** (rol distinto de `Chairperson`). La presidencia supone el 57 % de las filas (turnos de unas 26 palabras de media) y su género solo consta en el 25,5 %, así que se excluye de numeradores y denominadores. En las métricas de posición tampoco se cuentan las **continuaciones** (un discurso partido por una interrupción breve de la presidencia cuenta como un solo turno).

## Métricas de presencia

Valores de referencia sobre ParlaMint-ES 5.0 (2015 a feb. 2023), calculados sobre todo el corpus.

| Id | Métrica | Definición | Referencia | Fuente |
|---|---|---|---|---|
| P1 | Proporción de oradoras | Oradoras distintas / oradores distintos | 41,7 % | Metadatos |
| P2 | Proporción de intervenciones | Intervenciones de mujeres / total de oradores | 37,4 % | Metadatos |
| P3 | Proporción de palabras | Palabras de mujeres / total de palabras de oradores | 36,1 % | Metadatos + texto |
| P4 | Intervenciones por persona | Media de intervenciones por oradora y por orador | 31,7 / 38,0 | Metadatos |

P1 y P2 miden cosas distintas: P1 cuenta personas y P2 cuenta veces que se toma la palabra. Que P1 sea mayor que P2 indica que, de media, cada mujer interviene menos veces que cada hombre. Que P3 sea menor que P2 indica que sus intervenciones son algo más cortas (548 frente a 580 palabras de media).

## Métricas de protagonismo

| Id | Métrica | Definición | Método | Fuente |
|---|---|---|---|---|
| R1 | Apertura | % de secciones del orden del día cuyo **primer** turno de orador es de una mujer, frente a la proporción de mujeres entre todos los turnos de esas secciones | Conteo | Metadatos + XML |
| R2 | Cierre | Igual que R1, con el **último** turno de la sección | Conteo | Metadatos + XML |
| R3 | Moderación | **Excluida de las métricas principales.** El género de la presidencia consta solo en el 25,5 % de los turnos y de forma irregular: por año, entre el 10 % y el 35 % de turnos con género, y entre el 14 % y el 84 % de mujeres entre ellos. No es una muestra representativa. Se documenta como dato exploratorio | — | Metadatos |
| R4 | Intervenciones largas | Proporción de mujeres entre el 25 % de intervenciones más largas (referencia: 37,4 %, umbral de 836 palabras) | Conteo | Texto |
| R5 | Posición en el debate | Posición media de los turnos de cada género dentro de su sección, de 0 (primer turno) a 1 (último). Se calcula también **dentro de cada grupo parlamentario** | Conteo | Metadatos + XML |
| R6 | Reacciones del hemiciclo | Aplausos, rumores o protestas y risas por 1.000 palabras, según el género de quien habla y comparando dentro del mismo grupo o estatus. Salen de los comentarios del transcriptor entre `[[ ]]`, clasificados con reglas (cubren cerca del 70 % de las ocurrencias como reacciones; la mayor parte del resto son pausas y restos que no son reacciones) | Reglas | Texto |
| R7 | Rol en el debate | Función de cada intervención: `defensa` de una iniciativa, `pregunta` o interpelación, `respuesta`, `replica`, fijación de `posicion`, `procedimental` u `otra`. Se compara la proporción de cada rol entre mujeres y hombres | **IA** (método híbrido) | Texto |

Para R1 y R2, la **razón de representación** es la cuota de mujeres en la apertura o el cierre dividida entre la referencia: 1 es proporcional, más de 1 indica que abren o cierran más de lo que les correspondería por su presencia, y menos de 1, menos.

## Métrica de contenido

| Id | Métrica | Definición | Fuente |
|---|---|---|---|
| T1 | Reparto temático | % de mujeres en cada tema respecto de la media (37,4 %) | `Topic` |

Ejemplo observado: Social Welfare 51,6 % frente a International Affairs 26,9 %. Antes de usarla hay que comprobar cómo se asigna `Topic` (parece automático) y qué pasa con los temas con pocos casos.

## Dónde entra la IA

Presencia, apertura, cierre y posición salen contando metadatos, y las reacciones (R6) se resuelven bien con reglas: 48 comentarios distintos suman el 82,6 % de las ocurrencias. Usar un modelo de lenguaje ahí aportaría poco, y es mejor decirlo que forzarlo.

La IA se usa donde hace falta **entender el texto**: el **rol en el debate (R7)**. Los metadatos no dicen si alguien presenta una iniciativa, pregunta al Gobierno o solo fija la posición de su grupo, y las reglas de palabras clave lo resuelven mal: en la evaluación no detectaron ninguna `defensa` y se equivocaron más del doble con las intervenciones de mujeres. Un sistema sin IA infravaloraría justo el protagonismo de las mujeres.

Diseño (detalles en `05-evaluacion.md` y `06-acuerdo-y-confirmacion.md`):

- **Método híbrido:** si la `secuencia` de turnos muestra que la persona ya había hablado en el intercambio, el turno es `replica` por regla (determinista y explicable); el resto lo decide un modelo abierto (Qwen3.5-397B-A17B) accesible por una API compatible con OpenAI y sustituible por otro con un parámetro.
- **Evaluación** contra una muestra anotada a mano y a ciegas, comparada con las reglas como referencia (*baseline*), con acuerdo entre anotadoras (kappa de Cohen) y confirmación en filas nuevas. Se mide el **error por género**, no solo el acierto global.
- **Privacidad por diseño:** el modelo no recibe nombre, grupo ni género; el género se une después por el identificador de la intervención.
- **Alcance:** las **26.586 intervenciones** de diputadas y diputados (rol `Regular`, sin continuaciones ni las 120 anotadas a mano), clasificadas con los AI Endpoints de OVHcloud: 7.051 por la regla estructural y 19.535 por el modelo, sin ninguna fila sin respuesta. Antes se usó una muestra estratificada de 3.000 (1.500 por género, con pesos), que sirvió para validar el diseño muestral (ver más abajo).

Estimar el género de la presidencia a partir del texto queda descartado: sería una inferencia sobre personas, con riesgo ético y de error, y no es necesaria.

## Alcance de cada métrica

| Métricas | Sobre qué se calculan | Método |
|---|---|---|
| P1–P4 | Todo el corpus (76.369 intervenciones; 32.541 de oradores) | Conteo |
| R1, R2, R5 | Todo el corpus: 1.271 secciones con 2 o más turnos de oradores | Conteo |
| R4 | Todo el corpus | Conteo |
| R6 | Todo el corpus (provisional) | Reglas |
| R7 | Todo el corpus de diputadas y diputados (26.586 intervenciones) | IA (híbrido) |
| T1 | Todo el corpus (exploratoria) | Metadatos |

## Resultados de posición en el debate (R1, R2, R5)

Todo el corpus, por sección del orden del día. Intervalos de Wilson del 95 %. Referencia: proporción de mujeres entre los turnos de esas mismas secciones.

| Métrica | Mujeres | Referencia | Razón |
|---|---|---|---|
| R1 Apertura | 39,9 % [37,2–42,6] | 36,7 % | 1,09 |
| R2 Cierre | 43,5 % [40,8–46,3] | 36,7 % | 1,19 |
| R1 Apertura, sin ministros | 37,8 % [35,2–40,5] | 33,7 % | 1,12 |
| R2 Cierre, sin ministros | 40,9 % [38,2–43,6] | 33,7 % | 1,21 |

| R5 Posición media (0 = primero, 1 = último) | Mujeres | Hombres |
|---|---|---|
| Todas las intervenciones | 0,522 [0,516–0,528] | 0,487 [0,482–0,491] |
| Sin ministros | 0,527 [0,520–0,533] | 0,486 [0,482–0,491] |

**Por tipo de sección**, el orden de palabra lo marca el reglamento y se nota:

| Sección | R1 razón | R2 razón | Nota |
|---|---|---|---|
| Preguntas | 0,83 | 1,34 | Suele abrir el líder de la oposición |
| Interpelaciones urgentes | 0,94 | 1,12 | |
| Mociones consecuencia de interpelaciones | 1,09 | 1,15 | |
| Proposiciones no de ley | 1,20 | 1,09 | |
| Toma en consideración de proposiciones | 1,37 | 1,43 | |
| Debates de totalidad | 1,40 | 1,17 | |
| Convalidación o derogación de reales decretos | 1,26 | 1,26 | |

**R5 dentro de cada grupo parlamentario** (sin ministros, grupos con al menos 200 turnos de cada género):

| Grupo | Mujeres | Hombres | Diferencia |
|---|---|---|---|
| PSOE | 0,604 | 0,483 | Grande |
| UP | 0,566 | 0,516 | Pequeña |
| ERC-S | 0,559 | 0,512 | Dudosa |
| PP | 0,553 | 0,535 | No clara (intervalos solapados) |
| Vox | 0,564 | 0,543 | No clara |
| Cs | 0,469 | 0,485 | No clara |
| EAJ-PNV | 0,485 | 0,455 | No clara |
| JxCat-Junts | 0,476 | 0,487 | No clara |
| EH Bildu | 0,421 | 0,469 | No clara |

### Lectura

- Las mujeres **abren y cierran secciones al menos en proporción a su presencia**, y algo más en los cierres. No aparecen relegadas a los turnos intermedios. Ocurre también sin contar a las ministras.
- En el conjunto, las mujeres hablan algo más tarde dentro de cada sección. Pero **esa diferencia no es un patrón general de género**: dentro de cada grupo parlamentario se concentra en el PSOE (y en menor medida en UP) y no aparece en la mayoría. Lo más probable es que refleje la **organización interna de cada grupo** (quién es portavoz en cada debate) y el orden del reglamento (los grupos grandes, y el del Gobierno, suelen intervenir al final). Estos datos no permiten afirmar la causa.
- Encaja con lo observado en el rol en el debate: **la brecha está en cuánto intervienen las mujeres (37 % de las intervenciones), no en qué papel cumplen ni en qué momento hablan**.
- Por año hay altibajos sin una tendencia clara; 2016, 2019 y 2023 tienen pocas secciones.

Reproducción (desde la raíz del repositorio, con los datos descargados según `data/README.md`):

```bash
python src/presencia/posicion.py data/raw/ParlaMint-ES.txt --tei data/raw/ParlaMint-ES.TEI
```

Escribe `data/processed/posicion_resumen.csv` (métricas agregadas) y `data/processed/puntos.csv` (una fila por sección, sin nombres).

## Resultados del rol en el debate (R7)

Todo el corpus de diputadas y diputados, clasificado con el método híbrido. Porcentaje de las intervenciones de cada género que cumplen cada rol, con intervalo de Wilson del 95 %. Razón = cuota de mujeres en el rol / cuota de mujeres en el grupo (1 = proporcional).

**Diputadas y diputados, sin ministros** (mujeres n = 7.686, hombres n = 15.105; 33,7 % de mujeres):

| Rol | Mujeres | Hombres | Razón |
|---|---|---|---|
| Defensa de una iniciativa | **8,4 %** [7,8–9,0] | 6,5 % [6,1–6,9] | **1,17** |
| Pregunta al Gobierno | **11,0 %** [10,3–11,7] | 9,0 % [8,6–9,5] | **1,13** |
| Respuesta | 2,0 % [1,7–2,3] | 2,7 % [2,5–3,0] | 0,80 |
| Réplica | 20,0 % [19,1–20,9] | 21,3 % [20,7–22,0] | 0,96 |
| Fijación de posición | 54,5 % [53,3–55,6] | **57,0 %** [56,2–57,8] | 0,97 |
| Procedimental | 4,2 % [3,8–4,6] | 3,4 % [3,1–3,7] | 1,15 |

**Por estatus:**
- **Oposición** (mujeres n = 5.849, hombres n = 11.355): defensa 8,4 % frente a 6,7 %; pregunta 12,7 % frente a 10,8 %; fijación de posición 55,8 % frente a 60,3 %.
- **Gobierno y socios** (mujeres n = 1.701, hombres n = 3.245): defensa 8,3 % frente a 5,9 %; pregunta 6,0 % frente a 4,1 %; réplica 23,7 % frente a 31,8 %.
- **Miembros del Gobierno** (mujeres n = 2.084, hombres n = 1.711): las ministras hacen el **54,9 %** de las intervenciones del Gobierno y cumplen los mismos papeles que los ministros (respuesta 31,0 % frente a 30,1 %; réplica 61,8 % frente a 63,5 %).

**Validación del diseño muestral.** Las estimaciones de la muestra estratificada de 3.000 contenían el valor real del corpus completo en los 7 roles (por ejemplo, defensa: muestra 8,7 % [7,2–10,5], corpus 8,4 %; pregunta: muestra 10,6 % [9,0–12,5], corpus 11,0 %).

### Lectura

- Las diputadas intervienen menos (37 % de las intervenciones), pero **cuando intervienen ocupan algo más los papeles de protagonismo**: presentan más iniciativas y preguntan más al Gobierno. Los diputados, en proporción, fijan más la posición de su grupo. El patrón se repite en la oposición y en el Gobierno y sus socios.
- Las **ministras** son mayoría de las intervenciones del Gobierno en el periodo y cumplen los mismos papeles que los ministros.
- Junto con la posición (R1, R2, R5): las mujeres abren y cierran secciones al menos en proporción a su presencia. **La brecha principal está en cuánto intervienen**; cuando lo hacen, no quedan relegadas a papeles secundarios.

### Cautelas

- **No comparar con la tabla de «todas» las intervenciones:** mezcla ministros y diputados, y como hay más ministras, parece que las mujeres fijan menos posición (42,9 % frente a 51,2 %). Es un efecto de composición: los miembros del Gobierno no fijan la posición de un grupo.
- **Diferencias pequeñas** (unos 2 puntos) frente al error del clasificador (acierta en torno al 87 % de los roles en filas nuevas). Son creíbles porque el error es similar para mujeres y hombres, y en la duda de `defensa` la segunda anotadora confirmó que los casos ambiguos eran defensas de mujeres (`06-acuerdo-y-confirmacion.md`). Aun así, se presentan como diferencias pequeñas pero consistentes.
- Los datos no dicen **por qué** ocurren (reparto de portavocías, ponencias, estrategia de los grupos…).
- Las razones de roles con casi ningún caso (por ejemplo, «pregunta» entre ministros, u «otra») no tienen significado.

Reproducción:

```bash
python src/presencia/classify.py data/raw/ParlaMint-ES.txt --n 0 --paralelo 4 --salida data/processed/roles_completo.csv
python src/presencia/roles.py data/processed/roles_completo.csv --salida data/processed/roles_resumen_completo.csv
```

Con la caché del modelo (`data/processed/llm/Qwen3.5-397B-A17B.jsonl`) en el repositorio, la clasificación se reproduce sin llamar a la API.

## Limitaciones a declarar

- Más tiempo de palabra no implica más influencia.
- El género procede de los metadatos del corpus (`M`, `F`, `U`): no recoge otras identidades.
- La moderación no se puede medir de forma representativa.
- **Apertura y cierre se miden por sección del orden del día**, no por cada iniciativa o pregunta, porque el XML solo marca las secciones.
- **El orden de palabra lo fija el reglamento** (quién presenta, en qué orden intervienen los grupos), así que R1, R2 y R5 reflejan en parte qué cargos ocupan las mujeres, no solo cuándo se les da la palabra. Por eso se desglosan por tipo de sección y por grupo.
- Los turnos de una misma sección no son independientes: los intervalos reales son algo más anchos que los calculados.
- Hay muchas comparaciones (por tipo, año y grupo): alguna diferencia puede salir por azar. Solo se destacan diferencias grandes y consistentes.
- Los porcentajes por año y por tema dependen del número de casos; 2016, 2019, 2023 y varios temas tienen pocos.
- Los aplausos dependen del grupo político: sin controlarlo, la comparación por género engaña.
- Los datos terminan en febrero de 2023.

## Hoja de ruta

- **Apertura y cierre por iniciativa:** dividir cada sección en iniciativas usando los anuncios de la presidencia o el rol `defensa`/`pregunta` que ya clasifica la IA.
- **Error de la métrica agregada:** comparar, en la muestra anotada, el % de cada rol por género según las personas y según el sistema (criterio de éxito del taller de la organización).
- **Cruce de posición y rol:** de las secciones que abre una mujer, qué papel cumple (`puntos.csv` guarda el identificador de la intervención de apertura y de cierre).
- **Interrupciones** dadas y recibidas, y **menciones** (a quién se nombra y cómo), propuestas en el taller de la organización.
- Limpiar R6 y validar `Topic` (T1).
