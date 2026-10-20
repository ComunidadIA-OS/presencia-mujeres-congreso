# Datos

> **Estado:** corpus explorado con `src/presencia/explore.py` (20/10/2026). Pendiente: explorar el texto de las intervenciones.

## Fuente principal

**ParlaMint-ES 5.0** (CLARIN.SI, CC BY 4.0 según su ficha): sesiones plenarias del **Congreso de los Diputados**, del 01/01/2015 al 23/02/2023 (parte final de la X legislatura y XI, XII, XIII y XIV hasta esa fecha). Textos y metadatos de los diputados proceden de la web oficial del Congreso.

## Fuente secundaria (opcional)

Corpus regionales de ParlaMint (Cataluña, Galicia, País Vasco) o **ParlaMintCAT** (CORA, CC BY 4.0 según su ficha).

## Estructura de los archivos

- Cada sesión tiene un `.txt` (ID de la intervención y texto, separados por tabulador; comentarios del transcriptor entre `[[ ]]`) y **dos TSV de metadatos**: uno con valores en inglés y otro en español.
- Los dos TSV **comparten los nombres de columna** y solo cambian los valores (`Chairperson` / `Presidencia`, `Macroeconomics` / `Macroeconomía`). El código usa solo el inglés; si se leen ambos, todo se cuenta doble.
- Una fila = una intervención. Columnas: `Text_ID`, `ID`, `Title`, `Date`, `Body`, `Term`, `Session`, `Meeting`, `Sitting`, `Agenda`, `Subcorpus`, `Lang`, `Speaker_role`, `Speaker_MP`, `Speaker_minister`, `Speaker_party`, `Speaker_party_name`, `Party_status`, `Party_orientation`, `Speaker_ID`, `Speaker_name`, `Speaker_gender`, `Speaker_birth`, `Topic`.
- `Speaker_role`: `Chairperson`, `Regular`, `Guest`. `Speaker_gender`: `M`, `F`, `U` (desconocido) y `-` (sin dato).
- No hay columna con el número de palabras: se calcula desde el `.txt`.
- Algunas filas tienen menos columnas que la cabecera; el código las trata como valor desconocido.

## Resultados de la exploración (ParlaMint-ES 5.0)

**Tamaño:** 450 sesiones, 76.369 intervenciones: presidencia 43.630 (57 %), diputados/as (`Regular`) 32.551, invitados/as (`Guest`) 188.

**Oradores (sin presidencia):** 32.739 intervenciones; mujeres 12.240, hombres 20.488, desconocido 11. **Mujeres: 37,4 %** de las intervenciones.

**Personas distintas:** 386 mujeres y 539 hombres (41,7 % mujeres). Intervenciones por persona, calculadas a partir de los totales: 31,7 por mujer y 38,0 por hombre.

**Evolución por año** (% de mujeres en las intervenciones de oradores; n = intervenciones con género M o F):

| Año | % mujeres | n |
|---|---|---|
| 2015 | 30,8 | 3.890 |
| 2016 | 29,7 | 1.841 |
| 2017 | 33,8 | 4.203 |
| 2018 | 39,8 | 5.033 |
| 2019 | 40,6 | 1.366 |
| 2020 | 36,8 | 5.081 |
| 2021 | 40,1 | 5.584 |
| 2022 | 41,8 | 4.979 |
| 2023 | 43,1 | 751 |

2016, 2019 y 2023 tienen pocos datos (legislaturas cortas y 2023 solo hasta febrero).

**Presidencia:** el género consta en solo el **25,5 %** de los turnos (3.353 mujeres, 7.794 hombres, 32.483 sin dato). Por año, el porcentaje con género conocido va del 9,7 % al 34,7 % y el % de mujeres entre los conocidos oscila entre el 13,9 % y el 83,7 %. No es una muestra representativa (ver `01-metricas.md`, R3).

**Ministros:** 4.460 de las 32.739 intervenciones de oradores (13,6 %). El campo está completo para oradores. Pendiente comprobar su fiabilidad por año (en la sesión de 2015 revisada figuraban como `notMinister` personas que, por lo que recuerdo, eran ministras/ministros).

**Temas** (% de mujeres; media 37,4 %). Más altos: Social Welfare 51,6 (n=850), Labor 46,8, Health 45,7, Education 44,9, Civil Rights 44,9. Más bajos: International Affairs 26,9 (n=1.251), Law and Crime 28,7, Government Operations 29,2, Culture 29,8, Transportation 32,0. Algunos temas tienen muy pocos casos (Foreign Trade n=49, Public Lands n=150).

## Limitaciones

| Hallazgo | Consecuencia |
|---|---|
| Género de la presidencia conocido solo en el 25,5 % de los turnos, de forma irregular | La moderación no se usa como métrica principal |
| Género binario (`M`, `F`) más `U` en 11 casos | No recoge otras identidades |
| `Topic` parece asignado de forma automática (método sin verificar) | No tratarlo como verdad de referencia hasta comprobarlo |
| Solo consta el grupo parlamentario, no el partido | Análisis por grupo |
| Control de calidad con ChatGPT y revisión manual (README oficial) | Posibles errores residuales |
| Datos hasta febrero de 2023 | No reflejan la composición actual |

## Pendiente

- [ ] Explorar el texto: formato real, longitud de las intervenciones y comentarios `[[ ]]`
- [ ] Comprobar `Speaker_minister` por año
- [ ] Comprobar cómo se asigna `Topic` en la documentación de la versión 5.0
- [ ] Confirmar la licencia (CC BY 4.0) en la página de CLARIN.SI
