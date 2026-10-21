# Datos

> **Estado:** corpus explorado con `src/presencia/explore.py` (metadatos) y `src/presencia/export.py` (texto), 20 y 21/10/2026.

## Fuente principal

**ParlaMint-ES 5.0** (CLARIN.SI, CC BY 4.0 según su ficha): sesiones plenarias del **Congreso de los Diputados**, del 01/01/2015 al 23/02/2023 (parte final de la X legislatura y XI, XII, XIII y XIV hasta esa fecha). Textos y metadatos de los diputados proceden de la web oficial del Congreso.

## Fuente secundaria (opcional)

Corpus regionales de ParlaMint (Cataluña, Galicia, País Vasco) o **ParlaMintCAT** (CORA, CC BY 4.0 según su ficha).

## Estructura de los archivos

- Cada sesión tiene un `.txt` (ID de la intervención, tabulador y texto, una intervención por línea; comentarios del transcriptor entre `[[ ]]`) y **dos TSV de metadatos**: uno con valores en inglés y otro en español.
- Los dos TSV **comparten los nombres de columna** y solo cambian los valores (`Chairperson` / `Presidencia`, `Macroeconomics` / `Macroeconomía`). El código usa solo el inglés; si se leen ambos, todo se cuenta doble.
- Una fila = una intervención. Columnas: `Text_ID`, `ID`, `Title`, `Date`, `Body`, `Term`, `Session`, `Meeting`, `Sitting`, `Agenda`, `Subcorpus`, `Lang`, `Speaker_role`, `Speaker_MP`, `Speaker_minister`, `Speaker_party`, `Speaker_party_name`, `Party_status`, `Party_orientation`, `Speaker_ID`, `Speaker_name`, `Speaker_gender`, `Speaker_birth`, `Topic`.
- `Speaker_role`: `Chairperson`, `Regular`, `Guest`. `Speaker_gender`: `M`, `F`, `U` (desconocido) y `-` (sin dato). `Speaker_party` contiene el **grupo parlamentario**.
- Los archivos están en UTF-8. PowerShell puede mostrar mal las tildes, pero los datos están bien.
- Algunas filas tienen menos columnas que la cabecera; el código las trata como valor desconocido.
- La unión metadatos-texto por `ID` funciona para las 76.369 intervenciones (0 sin texto).

## Resultados: metadatos

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

**Por grupo parlamentario** (% de mujeres en las intervenciones; n = intervenciones de oradores): PSOE 50,9 (6.258), UP 43,2 (2.214), EH Bildu 46,1 (800), PP 38,0 (6.367), ERC 36,0 (1.287), Cs 35,8 (2.428), Vox 32,2 (1.888), JxCat-Junts 30,7 (1.051), EAJ-PNV 24,8 (1.853). Las diferencias entre grupos son grandes y reflejan su composición, no su comportamiento. Por eso las comparaciones de reacciones deben hacerse dentro del mismo grupo o estatus.

**Presidencia:** el género consta en solo el **25,5 %** de los turnos (3.353 mujeres, 7.794 hombres, 32.483 sin dato). Por año, el porcentaje con género conocido va del 9,7 % al 34,7 % y el % de mujeres entre los conocidos oscila entre el 13,9 % y el 83,7 %. No es una muestra representativa (ver `01-metricas.md`, R3).

**Ministros:** 4.460 de las 32.739 intervenciones de oradores (13,6 %). El campo está informado en todos los años. % de mujeres entre las intervenciones de ministros: 2015 16,1; 2016 21,7; 2017 25,4; 2018 68,1; 2019 75,1; 2020 50,4; 2021 66,1; 2022 77,3; 2023 87,3. El salto de 2018 cuadra con la composición del Gobierno (por lo que recuerdo; verificar). En la sesión de 2015 revisada, algunos miembros del Gobierno figuraban como `notMinister`, así que puede haber omisiones.

**Temas** (% de mujeres; media 37,4 %). Más altos: Social Welfare 51,6 (n=850), Labor 46,8, Health 45,7, Education 44,9, Civil Rights 44,9. Más bajos: International Affairs 26,9 (n=1.251), Law and Crime 28,7, Government Operations 29,2, Culture 29,8, Transportation 32,0. Algunos temas tienen muy pocos casos (Foreign Trade n=49, Public Lands n=150).

## Resultados: texto

- **Palabras:** 19.750.359 en total; 18.603.032 en intervenciones de oradores. Media: 568 palabras por intervención de orador y 26 por turno de presidencia.
- **P3:** las mujeres suponen el **36,1 %** de las palabras de oradores (37,4 % de las intervenciones). Media de palabras por intervención: 548 (mujeres) y 580 (hombres); mediana 363 y 371.
- **R4:** entre el 25 % de intervenciones más largas (836 palabras o más), el 37,4 % son de mujeres, igual que su peso general.
- **Comentarios del transcriptor:** 77.757 en total, 8.563 distintos; 56.940 en intervenciones de oradores. Solo 48 comentarios distintos (más de 50 apariciones) suman el 82,6 % de las ocurrencias; 6.516 aparecen una sola vez.
- **Clasificación provisional por reglas** (% de ocurrencias): aplauso 55,4; pausa o procedimiento 15,5; rumor o protesta 12,0; risas 1,3; sin clase 15,8; el 3,4 % mezcla varias clases (`Rumores.-Aplausos`). Lo que queda sin clase son sobre todo cosas que no son reacciones: nombres de grupo (`[[EAJ-PNV]]`, 1.111), restos como `[[La señora]]` o `[[El señor]]`, y gestos (`[[Muestra un documento]]`, `[[Asentimiento]]`).
- **Comentarios por 1.000 palabras** (todos los tipos, resultado provisional): oposición, mujeres 2,86 y hombres 2,72; gobierno, mujeres 3,47 y hombres 3,65. Falta limpiar solo las reacciones y comprobar si las diferencias son apreciables.

## Limitaciones

| Hallazgo | Consecuencia |
|---|---|
| Género de la presidencia conocido solo en el 25,5 % de los turnos, de forma irregular | La moderación no se usa como métrica principal |
| Género binario (`M`, `F`) más `U` en 11 casos | No recoge otras identidades |
| `Topic` parece asignado de forma automática (método sin verificar) | No tratarlo como verdad de referencia hasta comprobarlo |
| Solo consta el grupo parlamentario, no el partido | Análisis por grupo |
| Control de calidad con ChatGPT y revisión manual (README oficial) | Posibles errores residuales |
| Datos hasta febrero de 2023 | No reflejan la composición actual |
| Los aplausos dependen del grupo | Comparar reacciones dentro del mismo grupo o estatus |

## Pendiente

- [ ] Decidir la tarea de IA (ver `01-metricas.md`)
- [ ] Limpiar la métrica de reacciones y comprobar la significación de las diferencias
- [ ] Comprobar cómo se asigna `Topic` en la documentación de la versión 5.0
- [ ] Confirmar la licencia (CC BY 4.0) en la página de CLARIN.SI
