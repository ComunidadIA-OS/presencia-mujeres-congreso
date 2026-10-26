# Evaluación del clasificador de roles

> **Estado:** resultados del 26/10/2026 sobre `data/annotated/muestra_anotada.csv`.

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

**Las reglas se equivocan más del doble con las intervenciones de mujeres.** El motivo es que en la muestra hay más preguntas e iniciativas de mujeres (7 preguntas frente a 2) y las reglas no detectan bien esos roles, que son justo los de protagonismo. Un sistema solo de reglas habría **infravalorado el protagonismo de las mujeres**. El modelo reduce esa brecha de error, aunque no la elimina del todo. Con 50 filas por género la diferencia es orientativa, y debe vigilarse en la confirmación con filas nuevas.

## Cautelas

- **Muestra pequeña.** Con 102 filas y clases de 4 a 9 casos, una fila cambia el F1 de una clase en más de 0,1. La ventaja sobre las reglas es clara. La diferencia entre modelos es indicativa.
- **El híbrido se eligió después de ver los errores** en este mismo conjunto. La regla de réplica ya existía en el *baseline* y no se ajustó, pero para confirmarlo sin sesgo hay que evaluarlo en filas nuevas (ver abajo).
- **Una sola anotadora.** Falta medir el acuerdo entre anotadoras (kappa de Cohen) con una segunda persona sobre unas 30 filas, que también sirven como conjunto de confirmación.
- **Igualdad de error por género.** Antes de comparar roles entre mujeres y hombres hay que comprobar que el clasificador no se equivoca más con un género que con otro (precisión y *recall* por género en la muestra anotada).
