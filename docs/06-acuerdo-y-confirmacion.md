# Acuerdo entre anotadoras y confirmación del método híbrido

> Complementa a `05-evaluacion.md`. Responde a dos de sus cautelas: había una sola anotadora (sin medida de acuerdo) y el método híbrido se eligió después de ver los errores del conjunto de evaluación.

## Diseño

Una segunda anotadora etiquetó **50 intervenciones a ciegas**, sin género, nombre ni grupo, siguiendo la guía v2 (`04-guia-anotacion.md`) y tras leer solo las 15 filas de calibración. Las 50 filas estaban mezcladas al azar, sin que supiera cuáles eran cuáles:

| Grupo | Filas | Para qué sirve |
|---|---|---|
| Ya anotadas por la anotadora 1 (de su conjunto de evaluación) | 20 | Acuerdo entre anotadoras (kappa de Cohen) |
| Nuevas, no vistas al diseñar el método (15 de mujeres, 15 de hombres) | 30 | Confirmar el método híbrido y su error por género |

Reproducción (desde la raíz del repositorio):

```bash
# 30 filas nuevas (no se solapan con las 120 de la anotadora 1)
python src/presencia/sample.py data/raw/ParlaMint-ES.txt --n 15 --semilla 2027 --salida data/processed/muestra_confirmacion.csv
# Acuerdo y confirmación
python src/presencia/agreement.py data/annotated/anotadora2.csv --modelo Qwen3.5-397B-A17B --paralelo 4 --errores
```

En el repositorio solo se publican los ID y las etiquetas (`data/annotated/anotadora2_etiquetas.csv`), no los textos. La confirmación usa una caché propia (`data/processed/llm/confirmacion/`), separada de la de la evaluación.

## Resultado 1: acuerdo entre anotadoras

| Medida | Valor |
|---|---|
| Filas comunes | 20 |
| Acuerdo observado | 16/20 (0,80) |
| **Kappa de Cohen** | **0,71** (sustancial, escala de Landis y Koch) |

Por etiqueta, el acuerdo es alto en `replica` (kappa 0,90) y `posicion` (0,74), y más bajo en `pregunta` y `respuesta` (0,44 cada una, con solo 2 casos por anotadora).

Los 4 desacuerdos responden a tres tipos de duda:

1. **Primer turno breve de quien pregunta (2 casos).** Ver el apartado siguiente.
2. **El Gobierno contesta o fija posición (1 caso):** un turno del Gobierno que responde a varios grupos al final de un debate (`respuesta` frente a `posicion`).
3. **Trámites muy cortos (1 caso):** una frase de una línea aceptando una enmienda (`procedimental` frente a `posicion`).

Lectura: la guía es suficientemente clara para que dos personas coincidan de forma sustancial, y las etiquetas de referencia son fiables. El acuerdo humano (0,80) marca además un techo realista para cualquier método automático.

## Patrón detectado: el primer turno breve

En dos filas, una del acuerdo y una de la confirmación, la secuencia del intercambio es:

```
A(24) P B(107) P → A(214)
C(22) P A(75) P → C(437)
```

El primer turno de quien pregunta es una pregunta ya formulada de unas 20 palabras, contesta el Gobierno, y el segundo turno de quien pregunta es largo y contiene más preguntas. Leído de forma aislada, ese segundo turno parece una `pregunta`. La guía v2 lo define como `replica`, porque es el segundo turno de la misma persona en el intercambio, y así lo etiquetan la regla estructural y la anotadora 1.

No es un fallo del método sino una ambigüedad de la guía. **No se ha cambiado ninguna etiqueta** para que coincida con el modelo. Propuesta para la guía v3:

> Si el primer turno de quien pregunta es breve (la pregunta ya formulada o «Doy por formulada la pregunta»), su siguiente turno en el mismo intercambio sigue siendo `replica`, aunque contenga nuevas preguntas.

No afecta a las métricas de protagonismo: la persona conserva su `pregunta` en el primer turno.

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

La evaluación se repitió en una segunda máquina (JupyterLab de OVHcloud) a partir del repositorio y de los datos descargados de la fuente oficial (MD5 verificado). Los 38 tests pasan y las cifras de `05-evaluacion.md` salen idénticas (reglas 0,873 / 0,683; Qwen 0,892 / 0,858; híbrido 0,922 / 0,888).

## Cautelas

- 20 filas para el kappa y 30 para la confirmación: los resultados son orientativos. Una fila mueve el kappa varias centésimas y el F1 de una clase en más de 0,1.
- Con 15 filas por género, la igualdad de error es una señal coherente con `05-evaluacion.md`, no una prueba estadística.
- La anotadora 2 conocía el proyecto, aunque no los resultados del sistema mientras anotaba.
