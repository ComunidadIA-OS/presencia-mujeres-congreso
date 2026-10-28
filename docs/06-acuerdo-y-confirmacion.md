# Acuerdo entre anotadoras y confirmación del método híbrido

> Complementa a `05-evaluacion.md`. Responde a tres de sus cautelas: había una sola anotadora (sin medida de acuerdo), el método híbrido se eligió después de ver los errores del conjunto de evaluación, y quedaba una duda sobre la clase `defensa`.
>
> **Actualizado el 27/10/2026** con un segundo lote de anotación (acuerdo sobre 34 filas y resolución de la duda de `defensa`).

## Diseño

Una segunda anotadora etiquetó **64 intervenciones a ciegas**, sin género, nombre ni grupo, siguiendo la guía v2 (`04-guia-anotacion.md`) y tras leer solo las 15 filas de calibración. Lo hizo en dos lotes, con las filas mezcladas al azar y sin saber cuáles eran cuáles:

| Lote | Grupo | Filas | Para qué sirve |
|---|---|---|---|
| 1 (26/10) | Ya anotadas por la anotadora 1 (de su conjunto de evaluación) | 20 | Acuerdo entre anotadoras (kappa de Cohen) |
| 1 (26/10) | Nuevas, no vistas al diseñar el método (15 de mujeres, 15 de hombres) | 30 | Confirmar el método híbrido y su error por género |
| 2 (27/10) | Casos dudosos de `defensa` aún no anotados por la anotadora 2 | 4 | Resolver la duda de `defensa` (ver abajo) |
| 2 (27/10) | Otras filas de la evaluación de la anotadora 1, al azar | 10 | Ampliar el acuerdo y ocultar cuáles eran las dudosas |

En total hay **34 filas comunes** con la anotadora 1 (una de las 5 dudosas ya estaba en el lote 1) y **30 nuevas**.

Reproducción (desde la raíz del repositorio):

```bash
# Lote 1: 30 filas nuevas (no se solapan con las 120 de la anotadora 1)
python src/presencia/sample.py data/raw/ParlaMint-ES.txt --n 15 --semilla 2027 --salida data/processed/muestra_confirmacion.csv
# Acuerdo y confirmación (archivo con los dos lotes juntos)
python src/presencia/agreement.py data/annotated/anotadora2_todo.csv --modelo Qwen3.5-397B-A17B --paralelo 4 --errores
```

El lote 2 se generó con la semilla 2028: las 4 dudosas pendientes y 10 filas al azar de la evaluación de la anotadora 1 que la anotadora 2 no había visto, mezcladas.

En el repositorio solo se publican los ID y las etiquetas (`data/annotated/anotadora2_etiquetas.csv`), no los textos. La confirmación usa una caché propia (`data/processed/llm/confirmacion/`), separada de la de la evaluación.

## Resultado 1: acuerdo entre anotadoras

| Medida | Lote 1 (20 filas) | **Total (34 filas)** |
|---|---|---|
| Acuerdo observado | 16/20 (0,80) | **26/34 (0,765)** |
| Kappa de Cohen | 0,71 | **0,675** (sustancial, escala de Landis y Koch) |

Por etiqueta (34 filas), el acuerdo es alto en `replica` (kappa 0,87), aceptable en `posicion` (0,68) y `procedimental` (0,65), y más bajo en `defensa` (0,53), `pregunta` y `respuesta` (0,47 cada una), con muy pocos casos por anotadora.

Los 8 desacuerdos responden a cuatro tipos de duda:

1. **Frontera entre `defensa` y `posicion` (3 casos).** Ver «La duda de `defensa`».
2. **Primer turno breve de quien pregunta (2 casos).** Ver el apartado siguiente.
3. **El Gobierno contesta o fija posición (1 caso):** un turno del Gobierno que responde a varios grupos al final de un debate (`respuesta` frente a `posicion`).
4. **Trámites muy cortos (1 caso):** una frase de una línea aceptando una enmienda (`procedimental` frente a `posicion`).

A estos se suma un caso marcado como `otra` por una anotadora y como `replica` por la otra.

Lectura: la guía permite que dos personas coincidan de forma sustancial, y las etiquetas de referencia son fiables. Los desacuerdos se concentran en fronteras concretas de la guía, que se aclaran en la propuesta de guía v3. El acuerdo humano (0,765) marca además un techo realista para cualquier método automático.

## El sistema frente a cada anotadora

En las mismas 34 filas comunes:

| Comparación | Acuerdo |
|---|---|
| Anotadora 1 frente a anotadora 2 | 26/34 = 0,765 |
| Híbrido frente a anotadora 1 | 29/34 = 0,853 |
| **Híbrido frente a anotadora 2** | **27/34 = 0,794** |

**El método híbrido coincide con cada anotadora tanto o más de lo que ellas coinciden entre sí:** su rendimiento está al nivel del acuerdo humano. La cifra frente a la anotadora 1 es algo optimista, porque el híbrido se eligió viendo los errores sobre sus etiquetas; la de la anotadora 2 es independiente.

## La duda de `defensa`

En la evaluación había **5 filas** en las que el modelo decía `defensa` y la anotadora 1 había anotado `posicion`, 4 de ellas de mujeres. Era relevante porque `defensa` es el único rol con una diferencia significativa entre mujeres y hombres en la muestra de 3.000 (8,7 % frente a 5,9 %): si el modelo sobrestimaba las defensas de las mujeres, esa diferencia la crearía el propio sistema.

La anotadora 2 las anotó a ciegas, mezcladas con otras filas:

| Caso | Género | Anotadora 1 | Modelo | Anotadora 2 |
|---|---|---|---|---|
| 2015-05-13 u277 | F | posicion | defensa | **defensa** |
| 2017-11-28 u63 | F | posicion | defensa | **defensa** |
| 2017-03-14 u64 | F | posicion | defensa | **defensa** |
| 2021-05-26 u141 | F | posicion | defensa | posicion |
| 2017-11-28 u5 | M | posicion | defensa | posicion |

- **En 3 de los 5 casos, la segunda anotadora coincide con el modelo.** No eran errores claros del modelo, sino casos ambiguos en los que dos personas discrepan.
- **En 2 casos, las dos anotadoras dicen `posicion`:** ahí el modelo sí se equivoca, y ve alguna `defensa` de más. Esos 2 errores son **uno de una mujer y uno de un hombre**: no hay sesgo de género en los errores confirmados.
- **Los 3 casos ambiguos son de mujeres.** Si en esta clase alguna referencia infravaloraba el protagonismo de las mujeres, era la anotación original, no el modelo.

**Conclusión:** la diferencia en `defensa` entre mujeres y hombres no es un artefacto del modelo. Con solo 5 casos es una señal, no una prueba. Las etiquetas de la anotadora 1 **no se han cambiado**: la evaluación de `05-evaluacion.md` se mantiene tal cual, y esta sección documenta la ambigüedad.

## Patrón detectado: el primer turno breve

En dos filas, una del acuerdo y una de la confirmación, la secuencia del intercambio es:

```
A(24) P B(107) P → A(214)
C(22) P A(75) P → C(437)
```

El primer turno de quien pregunta es una pregunta ya formulada de unas 20 palabras, contesta el Gobierno, y el segundo turno de quien pregunta es largo y contiene más preguntas. Leído de forma aislada, ese segundo turno parece una `pregunta`. La guía v2 lo define como `replica`, porque es el segundo turno de la misma persona en el intercambio, y así lo etiquetan la regla estructural y la anotadora 1.

No es un fallo del método sino una ambigüedad de la guía. **No se ha cambiado ninguna etiqueta** para que coincida con el modelo. No afecta a las métricas de protagonismo: la persona conserva su `pregunta` en el primer turno.

## Propuesta de guía v3

Dos reglas nuevas, surgidas de los desacuerdos:

> **Primer turno breve.** Si el primer turno de quien pregunta es breve (la pregunta ya formulada o «Doy por formulada la pregunta»), su siguiente turno en el mismo intercambio sigue siendo `replica`, aunque contenga nuevas preguntas.

> **`defensa` frente a `posicion`.** Es `defensa` el turno de quien **presenta** la iniciativa o la enmienda que se debate: la presidencia le da la palabra «para la presentación» o «para la defensa», y suele decir «presentamos», «traemos a esta Cámara» o «nuestra proposición/moción/enmienda». Es `posicion` el turno de un grupo que **opina** sobre una iniciativa de otro grupo, aunque defienda sus propias enmiendas a ella al fijar posición. En caso de duda, la pista es si la iniciativa que se debate es del grupo de quien habla.

Para aplicar la guía v3 habría que reanotar la muestra con ella. Queda en la hoja de ruta, junto con ampliar la muestra de confirmación.

## Resultado 2: confirmación en 30 filas nuevas

Referencia: etiquetas de la anotadora 2. Ejemplos para el modelo: las 15 filas de calibración de la anotadora 1.

| Método | Accuracy | F1 macro | Mujeres (n = 15) | Hombres (n = 15) |
|---|---|---|---|---|
| Reglas | 0,867 | 0,550 | 3 errores (0,80) | 1 error (0,93) |
| **Híbrido** (estructura + Qwen3.5-397B-A17B) | 0,867 | **0,694** | 2 errores (0,87) | 2 errores (0,87) |

- **En accuracy empatan.** 18 de las 30 filas son `posicion`, que las reglas ya resuelven, así que la accuracy apenas distingue los métodos.
- **El híbrido gana en los roles de protagonismo:** acierta la única `defensa`, que las reglas no detectan. Por eso sube el F1 macro.
- **El hallazgo de género se repite en un conjunto independiente:** las reglas se equivocan más con las mujeres (3 frente a 1) y con el híbrido la diferencia desaparece (2 y 2).
- **El híbrido baja de 0,922 a 0,867** respecto al conjunto en el que se diseñó. Es la caída esperable al medir en datos no vistos, y es la cifra que debe tomarse como estimación del rendimiento real.
- De los 4 errores del híbrido, uno es el patrón del primer turno breve y otro es una fila que la anotadora marcó como `otra`.

## Reproducibilidad

La evaluación se repitió en una segunda máquina (JupyterLab de OVHcloud) a partir del repositorio y de los datos descargados de la fuente oficial (MD5 verificado). Los tests pasan y las cifras de `05-evaluacion.md` salen idénticas (reglas 0,873 / 0,683; Qwen 0,892 / 0,858; híbrido 0,922 / 0,888).

## Cautelas

- 34 filas para el kappa y 30 para la confirmación: los resultados son orientativos. Una fila mueve el kappa varias centésimas y el F1 de una clase en más de 0,1.
- La duda de `defensa` se apoya en 5 casos: es una señal coherente, no una prueba.
- Con 15 filas por género, la igualdad de error en la confirmación es una señal coherente con `05-evaluacion.md`, no una prueba estadística.
- La anotadora 2 conocía el proyecto, aunque no los resultados del sistema mientras anotaba. En el lote 2 sabía que había casos dudosos entre `defensa` y `posicion`, pero no cuáles eran.
