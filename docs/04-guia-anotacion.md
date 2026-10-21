# Guía de anotación: rol de cada intervención

Objetivo: etiquetar a mano unas 120 intervenciones para evaluar el sistema (reglas frente a modelo de lenguaje). Esta anotación es la verdad de referencia, así que importa más la coherencia que la velocidad.

## Cómo se hace

1. Genera la muestra: `python src/presencia/sample.py data/raw/ParlaMint-ES.txt` crea `data/processed/muestra_anotacion.csv`.
2. Ábrela en Excel o en VS Code. Cada fila trae:
   - `previo_2`: final del turno anterior al anterior (suele ser la intervención de otra persona).
   - `previo_1`: turno inmediatamente anterior (casi siempre la presidencia, que anuncia qué toca).
   - `inicio`: primeras 120 palabras de la intervención; `final`: sus últimas 40 si es larga.
   - `palabras`: longitud total.
3. Rellena **`etiqueta`** con una de las etiquetas de abajo, escrita exactamente igual. Usa `notas` si dudas.
4. Anota **a ciegas**: el archivo no trae género, nombre ni grupo. No busques quién habla. Si el texto lo delata ("señora ministra"), no pasa nada, pero no lo uses como criterio.
5. Se etiqueta por la **función en el debate**, no por el tema. La pista principal es lo que anuncia la presidencia en `previo_1`.

## Ejemplo resuelto

Una fila real de la muestra (`ParlaMint-ES_2015-09-15-CD150915.u165`):

- `previo_1`: «Muchas gracias, señor Macias. Por el Grupo Parlamentario Socialista tiene la palabra el señor Moscoso del Prado.»
- `inicio`: «Señor ministro, ha hecho una intervención muy parecida a la de todos sus compañeros de Gobierno, comparando la foto de 2011…»

La presidencia anuncia el turno de un grupo, y la persona valora la exposición del ministro en nombre de su grupo. Etiqueta: `posicion`.

## Continuaciones (ya filtradas)

Cuando la presidencia interrumpe con una frase breve («Silencio, por favor», «Señoría, debe ir terminando»), el corpus parte el discurso en dos filas y la segunda empieza a mitad de frase. Son **continuaciones**: no son una intervención nueva. El script las detecta y **no las incluye en la muestra**. Si aun así te sale una que empieza a mitad de frase, márcala como `otra` y escribe «continuación» en `notas`.

## Consejo para Excel

Para no equivocarte al escribir: selecciona la columna `etiqueta`, ve a Datos > Validación de datos > Permitir: Lista, y en Origen escribe `defensa,pregunta,respuesta,replica,posicion,procedimental,otra` (con punto y coma si tu Excel lo pide). Al terminar, guarda como «CSV UTF-8 (delimitado por comas)».

## Etiquetas

| Etiqueta | Cuándo |
|---|---|
| `defensa` | Presenta o defiende una iniciativa: proposición de ley o no de ley, moción, enmienda, proyecto de ley o decreto-ley (también si lo presenta un ministro) |
| `pregunta` | Formula una pregunta oral o una interpelación al Gobierno |
| `respuesta` | Primera contestación a una pregunta o interpelación, normalmente del Gobierno |
| `replica` | Turno breve de réplica o dúplica dentro de un intercambio ya empezado, de quien preguntó o de quien contestó |
| `posicion` | Fija la posición de su grupo, interviene en un turno a favor o en contra, o explica el voto |
| `procedimental` | Cuestión de orden, alusiones, petición de palabra o turno meramente de trámite |
| `otra` | No encaja o no se puede decidir |

## Criterios para decidir

- Si la presidencia anuncia una pregunta o interpelación y la intervención la formula: `pregunta`. Si contesta: `respuesta`. Si es el segundo o tercer turno del mismo intercambio: `replica`.
- Si la presidencia anuncia el turno de fijación de posiciones de los grupos: `posicion`.
- Si la intervención abre un punto presentando la iniciativa: `defensa`.
- Entre dos etiquetas posibles, elige la más específica y anota la duda en `notas`.
- Usa `otra` antes que forzar una etiqueta. Un buen conjunto de evaluación tiene pocas dudas ocultas.

## Buenas prácticas

- Anota todas de una vez o en pocas sesiones, para mantener el criterio.
- Idealmente, una segunda persona anota la misma muestra sin ver tus etiquetas, y se calcula el acuerdo entre ambas. Si no es posible, se declara como limitación.
- Guarda el archivo como CSV UTF-8. Para publicar en el repositorio se subirán solo los ID y las etiquetas, no los textos.
