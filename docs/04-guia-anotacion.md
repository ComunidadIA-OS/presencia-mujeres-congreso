# Guía de anotación: rol de cada intervención

Objetivo: etiquetar a mano unas 120 intervenciones para evaluar el sistema (reglas frente a modelo de lenguaje). Esta anotación es la verdad de referencia, así que importa más la coherencia que la velocidad.

> **Versión 2** (22/10/2026), ajustada tras el piloto de las 15 primeras filas. Esas 15 son el **conjunto de calibración**: sirven para afinar esta guía y como ejemplos para el modelo, y **no se usan en la evaluación**. Las 105 restantes son el conjunto de evaluación.

## Cómo se hace

1. Genera la muestra: `python src/presencia/sample.py data/raw/ParlaMint-ES.txt` crea `data/processed/muestra_anotacion.csv`.
2. Ábrela en Excel. Cada fila trae:
   - `previo_2`: final del turno anterior al anterior (suele ser la intervención de otra persona).
   - `previo_1`: turno inmediatamente anterior (suele ser la presidencia, que anuncia qué toca).
   - `secuencia`: estructura de los turnos anteriores (ver abajo).
   - `inicio`: primeras 120 palabras de la intervención; `final`: sus últimas 40 si es larga.
   - `palabras`: longitud total.
3. Rellena **`etiqueta`** con una de las etiquetas de abajo, escrita exactamente igual. Usa `notas` si dudas.
4. Anota **a ciegas**: el archivo no trae género, nombre ni grupo. No busques quién habla. Si el texto lo delata («señora ministra»), no pasa nada, pero no lo uses como criterio.
5. Se etiqueta por la **función en el debate**, no por el tema ni por el tono. Una pregunta que suena a reproche sigue siendo una `pregunta`.

## Cómo leer `secuencia`

Resume los turnos anteriores sin decir quién es quién. Ejemplo:

`P(2) C(18) P(2) B(68) P(2) C(350) P(2) → B(283)`

- **P** es la presidencia. Las **letras** son personas distintas dentro de esa ventana (A, B, C…); **la misma letra es la misma persona**. Los números son palabras.
- La **flecha** señala el turno que estás etiquetando.
- Las interrupciones breves de la presidencia («Silencio, por favor») no se muestran, y las dos partes de un discurso partido se suman.

El ejemplo se lee así: C habla poco (18), B contesta (68), C vuelve a hablar mucho (350) y ahora habla B otra vez. Como **B ya había intervenido en este intercambio**, el turno marcado es una `replica`.

Pistas típicas:

- Cada turno de una persona distinta, con la presidencia en medio, y sin que nadie repita: turnos de grupos (`posicion`).
- Un turno corto de una letra, y a continuación una letra nueva que contesta: `pregunta` y luego `respuesta`.
- Una letra que **repite** dentro de un intercambio: `replica`.

## Etiquetas

| Etiqueta | Cuándo |
|---|---|
| `defensa` | **Abre** un punto presentando una iniciativa: proposición de ley o no de ley, moción, enmienda, proyecto de ley o decreto-ley (también si lo presenta un ministro). Solo el turno de presentación, no los posteriores |
| `pregunta` | Formula una pregunta oral o una interpelación al Gobierno |
| `respuesta` | **Primera** contestación a una pregunta o interpelación, o contestación del Gobierno a lo que han planteado los grupos en un debate |
| `replica` | **Segundo turno o posterior de la misma persona** dentro de un intercambio: réplica de quien preguntó o dúplica de quien contestó |
| `posicion` | Fija la posición de su grupo, interviene en un turno a favor o en contra, o explica el voto |
| `procedimental` | Cuestión de orden, alusiones, petición de palabra o turno meramente de trámite |
| `otra` | No encaja o no se puede decidir |

## Criterios para decidir

- Si la presidencia anuncia una pregunta o interpelación y la intervención la formula: `pregunta`.
- Si es la primera vez que habla quien contesta: `respuesta`. Si esa misma persona vuelve a hablar en el mismo intercambio: `replica`.
- Si la presidencia anuncia el turno de un grupo en un debate: `posicion`.
- Si la intervención abre el punto presentando la iniciativa: `defensa`. Un turno posterior del Gobierno en ese mismo debate, contestando a los grupos, es `respuesta`, no `defensa`.
- Entre dos etiquetas posibles, elige la más específica y anota la duda en `notas`.
- Usa `otra` antes que forzar una etiqueta. Un buen conjunto de evaluación tiene pocas dudas ocultas.

## Continuaciones y turnos seguidos

- Cuando la presidencia interrumpe con una frase breve, el corpus parte el discurso en dos filas y la segunda empieza a mitad de frase. Son **continuaciones**: el script las detecta y **no las incluye en la muestra**. Si aun así te sale una, márcala como `otra` y escribe «continuación» en `notas`.
- **Dos turnos seguidos sin presidencia en medio no son una continuación si son personas distintas**, aunque ambos empiecen dando las gracias. Fíjate en las letras de `secuencia`: letras distintas, personas distintas.

## Consejo para Excel

Selecciona la columna `etiqueta`, ve a Datos > Validación de datos > Permitir: Lista, y en Origen escribe las etiquetas separadas por el separador de tu Excel (punto y coma o coma): `defensa;pregunta;respuesta;replica;posicion;procedimental;otra`. Al terminar, guarda como «CSV UTF-8». Si tu Excel usa punto y coma, no pasa nada: el código detecta el separador.

## Buenas prácticas

- Anota todas de una vez o en pocas sesiones, para mantener el criterio.
- Idealmente, una segunda persona anota la misma muestra sin ver tus etiquetas, y se calcula el acuerdo entre ambas. Si no es posible, se declara como limitación.
- Las etiquetas de una persona no deben cambiarse para coincidir con las de un modelo: la evaluación compara el modelo con las etiquetas humanas.
- Para publicar en el repositorio se subirán solo los ID y las etiquetas, no los textos.
