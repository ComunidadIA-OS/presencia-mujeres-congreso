# Evaluación del clasificador de roles

> **Estado:** resultados del 26/10/2026. Evaluación sobre `data/annotated/muestra_anotada.csv` y aplicación a 3.000 intervenciones del corpus.

Gráficos (se regeneran con `python src/presencia/figures.py`): `docs/figuras/`.

## Montaje

- **Tarea:** asignar a cada intervención su función en el debate: `defensa`, `pregunta`, `respuesta`, `replica`, `posicion`, `procedimental` u `otra` (guía: `04-guia-anotacion.md`).
- **Muestra:** 120 intervenciones (60 de mujeres y 60 de hombres, al azar, semilla 42), anotadas **a ciegas** (sin género, nombre ni grupo). Las 15 primeras son de **calibración** (ejemplos para el modelo) y no se evalúan. Quedan **102 de evaluación**.
- **Entrada de todos los métodos:** la misma que vio la anotadora: turno anterior de la presidencia, otro turno previo, `secuencia` de turnos anonimizada, inicio y final del texto, y número de palabras.
- **Modelos:** abiertos, servidos en OVHcloud AI Endpoints mediante la API compatible con OpenAI, con `temperature = 0` y 15 ejemplos (*few-shot*).
- **Métrica principal:** F1 macro, que da el mismo peso a las clases pequeñas (`defensa` tiene 4 casos y `pregunta` tiene 9).

## Resultados

| Método | Accuracy | F1 macro |
|---|---|---|
| Reglas (*baseline*, sin IA) | 0,873 | 0,683 |
| gpt-oss-120b | 0,873 | 0,748 |
| Qwen3.5-397B-A17B | 0,892 | 0,858 |
| **Híbrido: estructura + Qwen3.5-397B-A17B** | **0,922** | **0,888** |
| Qwen3.5-9B | no completado | — |

![F1 macro por método](figuras/1_evaluacion_metodos.png)

- Las reglas aciertan las réplicas, porque la `secuencia` muestra si la persona ya había hablado. Fallan en lo que exige leer el texto: no detectan ninguna `defensa` y confunden preguntas y respuestas con fijaciones de posición.
- Qwen3.5-397B acierta todas las `pregunta`, `respuesta`, `defensa` y `procedimental`, pero tiende a ver demasiadas: 5 réplicas las etiqueta como `respuesta` y 5 posiciones como `defensa`.
- **El método híbrido** combina lo mejor de cada uno. La réplica se decide por la estructura de turnos (regla determinista y explicable) y el resto lo decide el modelo. Además, ahorra alrededor del 30 % de las llamadas al modelo.
- Qwen3.5-9B se descartó en modo razonamiento: 33 filas en una noche, con *timeouts*, en el endpoint gratuito. Queda pendiente una prueba sin razonamiento (`--sin-razonamiento`).

Para reproducirlo (usa la caché de `data/processed/llm/`, sin llamadas nuevas):

```
python src/presencia/evaluate.py data/annotated/muestra_anotada.csv --modelo Qwen3.5-397B-A17B --modelo gpt-oss-120b --hibrido --errores
```

## Error por género

El género no se mostró al anotar ni se envía al modelo. Se une después por el ID desde `data/processed/intervenciones.csv`.

| Método | Mujeres (n = 52) | Hombres (n = 50) |
|---|---|---|
| Reglas | 9 errores (acc. 0,83) | 4 errores (acc. 0,92) |
| Qwen3.5-397B-A17B | 6 errores (acc. 0,88) | 5 errores (acc. 0,90) |
| Híbrido | 5 errores (acc. 0,90) | 3 errores (acc. 0,94) |

![Error por género](figuras/2_error_por_genero.png)

**Las reglas se equivocan más del doble con las intervenciones de mujeres.** El motivo es que en la muestra hay más preguntas e iniciativas de mujeres (7 preguntas frente a 2) y las reglas no detectan bien esos roles, que son justo los de protagonismo. Un sistema solo de reglas habría **infravalorado el protagonismo de las mujeres**. El modelo reduce esa brecha de error, aunque no la elimina del todo. Con 50 filas por género la diferencia es orientativa, y debe vigilarse en la confirmación con filas nuevas.

## Cautelas

- **Muestra pequeña.** Con 102 filas y clases de 4 a 9 casos, una fila cambia el F1 de una clase en más de 0,1. La ventaja sobre las reglas es clara. La diferencia entre modelos es indicativa.
- **El híbrido se eligió después de ver los errores** en este mismo conjunto. La regla de réplica ya existía en el *baseline* y no se ajustó, pero para confirmarlo sin sesgo hay que evaluarlo en filas nuevas (ver abajo).
- **Una sola anotadora.** Falta medir el acuerdo entre anotadoras (kappa de Cohen) con una segunda persona sobre unas 30 filas, que también sirven como conjunto de confirmación.
- **Igualdad de error por género.** El error total es parecido (5 de 52 frente a 3 de 50), pero **no se reparte igual por clase**: ver «La duda de `defensa`».

## La duda de `defensa`

Hay 5 intervenciones en las que el modelo dice `defensa` y la anotación dice `posicion`, y 4 de ellas son de mujeres. En las 52 filas de mujeres, la anotación tiene 3 defensas y el modelo pone 7. Al revisar los casos, varios cumplen la definición de la guía («abre un punto presentando una iniciativa»). En uno, por ejemplo, la presidencia anuncia «Para la presentación de la iniciativa tiene la palabra la señora…» y la oradora empieza «presentamos a la consideración de la Cámara una iniciativa». En otros se defienden enmiendas, y la guía menciona las enmiendas dentro de `defensa` pero también dice «turno de un grupo en un debate: `posicion`».

Por tanto, **no se sabe si el error es del modelo o de la anotación**. Siguiendo la guía, las etiquetas humanas no se cambian para que coincidan con el modelo. Se resolverá así:

1. Una segunda persona anota a ciegas esos 5 casos junto con los 30 de la confirmación, sin saber qué dijo cada parte.
2. Se aclara en la guía la frontera entre presentar enmiendas (`defensa`) y fijar posición sobre ellas (`posicion`).

## Aplicación al corpus: rol por género

El método híbrido se aplicó con Qwen3.5-397B-A17B a **3.000 intervenciones** (1.500 de mujeres y 1.500 de hombres al azar, semilla 2026, rol `Regular`, sin continuaciones ni filas anotadas). Se resolvieron 822 por estructura (réplica) y 2.178 con el modelo. Tardó unas 6,6 horas con 4 peticiones simultáneas y razonamiento activado, y la mayor parte de los reintentos se debieron a conexiones cortadas por el servidor. Resultados: `data/processed/roles_resumen.csv` (`python src/presencia/roles.py data/processed/roles.csv`).

![Rol por género](figuras/3_roles_por_genero.png)

Diputadas y diputados, sin ministros/as (mujeres n = 1.181, hombres n = 1.345):

| Rol | Mujeres | Hombres | Prueba de diferencia |
|---|---|---|---|
| Fijación de posición | 54,2 % | 57,4 % | p = 0,12 |
| Réplica | 20,8 % | 22,4 % | p = 0,33 |
| Pregunta / interpelación | 10,6 % | 8,9 % | p = 0,15 |
| Defensa de iniciativa | 8,7 % | 5,9 % | p = 0,01, **pendiente de validar** |
| Procedimental | 3,6 % | 3,0 % | — |
| Respuesta | 2,0 % | 2,3 % | — |

**Lectura:** las mujeres hacen el 37 % de las intervenciones (presencia, P2), pero **cuando intervienen cumplen los mismos papeles que los hombres**. No aparecen relegadas a turnos de menor protagonismo. La brecha está en la cantidad de intervenciones, no en el tipo de rol. La única diferencia significativa (defensa) coincide con la clase dudosa y no se da por buena hasta resolverla.

Otros resultados, que son pistas y no conclusiones:

- **Ministras:** hacen el 54,5 % de las intervenciones ponderadas de miembros del Gobierno (el corpus incluye los gobiernos paritarios desde 2018). Responden y replican en la misma proporción que los ministros (respuesta 30,4 % frente a 33,5 %; réplica 61,1 % frente a 60,0 %).
- **Diputados/as del Gobierno y socios:** ellas replican menos (21,7 % frente a 30,1 %) y defienden más (10,7 % frente a 5,2 %), pero con unas 250 intervenciones por género y la duda de `defensa`.
- El total «todas» mezcla ministros/as y diputados/as. Las diferencias que aparecen ahí (por ejemplo, más «respuesta» en mujeres) se deben a la composición del Gobierno, no al rol. Por eso hay que usar los grupos separados.

**Cómo leer las cifras:** proceden de un clasificador con F1 macro de 0,89, no de una anotación humana. Los intervalos solo recogen el error de muestreo, no el de clasificación. El `peso` corrige la muestra 50/50 para estimar cuotas del corpus real (mujeres: 9.770 candidatas; hombres: 16.816).
