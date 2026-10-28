# Ética, perspectiva de género y cumplimiento normativo

> **Estado:** borrador del 27/10/2026. No es asesoramiento jurídico: antes de un despliegue real, el análisis normativo debe revisarlo una persona experta en protección de datos.

## 1. Principios

| Principio | Cómo se aplica en el proyecto |
|---|---|
| **Sin inferencia de género** | Se usa el género declarado en los metadatos del corpus (`M`, `F`; `U` en 11 casos). El sistema no deduce el género del nombre, del texto ni de la voz, y no estima el género de la presidencia cuando falta. |
| **Análisis agregado** | Mide la representación en conjunto (secciones, grupos, años, roles). No evalúa, puntúa ni clasifica a personas concretas, y no publica rankings individuales. |
| **Minimización y privacidad por diseño** | El modelo de lenguaje no recibe nombre, grupo ni género: solo el texto de la intervención, el turno anterior de la presidencia y una secuencia de turnos anonimizada (letras en lugar de personas). El género se une después por el identificador de la intervención, solo para calcular métricas y errores. `roles_completo.csv` no guarda el identificador de la persona (`Speaker_ID`) y `puntos.csv` no guarda nombres ni títulos. |
| **Reglas donde bastan, IA donde aporta** | Presencia, apertura, cierre y posición se calculan contando metadatos. La IA solo se usa para el rol en el debate, donde las reglas fallan y, además, se equivocan más con las mujeres. |
| **Transparencia y reproducibilidad** | Código abierto (MIT), datos descargables de su fuente oficial con verificación MD5, métricas, prompts, evaluación y limitaciones documentados. Cada predicción indica si la decidió una regla o el modelo. |
| **Supervisión humana** | Las etiquetas de referencia son humanas, anotadas a ciegas, y no se cambian para que coincidan con el modelo. Los resultados se revisan antes de publicarse. |

## 2. Perspectiva de género

La perspectiva de género no se limita a la pregunta que responde el sistema; se aplica también **al propio sistema**:

- **Error por género como métrica de equidad.** No basta con el acierto global: se mide cuántos errores comete cada método con intervenciones de mujeres y de hombres. Las reglas se equivocaban más del doble con las mujeres (9 errores frente a 4 en el conjunto de diseño; 3 frente a 1 en la confirmación); el método híbrido reduce la brecha (5 frente a 3) y en la confirmación la elimina (2 y 2). Un sistema sin IA habría infravalorado el protagonismo de las mujeres, porque los roles que peor detectan las reglas (defensa de iniciativas, preguntas) son roles de protagonismo.
- **Muestreo con el mismo número por género.** La muestra estratificada toma 1.500 intervenciones de mujeres y 1.500 de hombres para que las estimaciones de ambos grupos tengan la misma precisión. Una muestra proporcional dejaría peor medidas a las mujeres. Los pesos corrigen esa sobrerrepresentación al estimar el corpus.
- **Anotación a ciegas.** Las personas que anotaron no veían género, nombre ni grupo.
- **Lectura sin estereotipos.** Los resultados se interpretan con controles (por tipo de sección, por grupo parlamentario, sin ministros) para no atribuir al género lo que se debe al reglamento o a la organización de los grupos. Por ejemplo, la diferencia en la posición media en el debate se concentra en un grupo y no es un patrón general.
- **Más tiempo de palabra no es más influencia.** Se declara como limitación en todos los resultados.
- **Género binario.** Los metadatos solo recogen `M` y `F` (y `U`). El sistema no puede analizar otras identidades y no lo intenta.

## 3. Marco normativo

### 3.1 Protección de datos (RGPD y LOPDGDD)

Las intervenciones parlamentarias son públicas, pero el nombre, el género y el grupo parlamentario de quien habla siguen siendo **datos personales**. Además, el grupo parlamentario revela **opiniones políticas**, una categoría especial de datos (art. 9 RGPD).

| Aspecto | Análisis |
|---|---|
| Personas afectadas | Diputadas, diputados y miembros del Gobierno, en el ejercicio de su cargo público |
| Base jurídica (art. 6) | Misión de interés público o interés legítimo en el análisis de la representación de las mujeres en una institución pública (a concretar según quién despliegue el sistema) |
| Categoría especial (art. 9) | Datos que la persona ha hecho manifiestamente públicos (art. 9.2.e), al intervenir en sesiones públicas del Congreso; y fines de investigación o estadísticos con garantías (art. 9.2.j y art. 89) |
| Minimización | El modelo no recibe datos identificativos; los resultados que se publican son agregados |
| Derechos | Información sobre el tratamiento en la documentación pública; canal para ejercer derechos (acceso, rectificación, oposición) en un despliegue real |
| Encargado del tratamiento | Si se usa un proveedor de IA en la nube (OVHcloud AI Endpoints), contrato de encargo del tratamiento (art. 28) y comprobación de que el tratamiento se hace en la UE |
| Evaluación de impacto | Recomendable antes de un despliegue real (tratamiento sistemático de datos de categoría especial, aunque sean públicos) |

**Qué se publica en el repositorio.** Código, documentación, métricas agregadas y, de la anotación, solo identificadores de intervención y etiquetas. Los identificadores ya son públicos en ParlaMint. Pendiente de decidir: si se publican los fragmentos de texto de la muestra anotada (la licencia CC BY 4.0 lo permite con atribución) y los archivos por intervención (`roles_completo.csv`, `puntos.csv`).

### 3.2 Reglamento europeo de IA (Reglamento (UE) 2024/1689)

| Pregunta | Respuesta |
|---|---|
| ¿Práctica prohibida (art. 5)? | No. No manipula, no puntúa socialmente a personas, no categoriza biométricamente ni infiere atributos sensibles: usa el género declarado en los metadatos. |
| ¿Alto riesgo (Anexo III)? | No, según nuestro análisis. El caso más cercano es el de los sistemas destinados a influir en el resultado de elecciones o en el voto (Anexo III, punto 8.b). Este sistema no está destinado a eso: produce indicadores agregados sobre la representación en debates pasados para análisis institucional, académico o periodístico. Si algún día se usara para orientar campañas o el voto, habría que revisar la clasificación. |
| Obligaciones aplicables | **Alfabetización en IA** (art. 4) de quien lo use. **Transparencia**: los informes deben indicar que los roles se han clasificado con un modelo de IA y con qué precisión. Buenas prácticas voluntarias: documentación técnica, registro de predicciones, supervisión humana. |
| Modelo de propósito general | El proyecto **usa** un modelo de propósito general (Qwen3.5-397B-A17B), no lo comercializa, así que no le corresponden las obligaciones de proveedor de modelos de propósito general. |
| Calendario | El Reglamento (UE) 2026/1744 («Ómnibus Digital») retrasa las obligaciones de alto riesgo del Anexo III al 2 de diciembre de 2027. Las de transparencia se aplican desde el 2 de agosto de 2026. |

### 3.3 Licencias

| Componente | Licencia |
|---|---|
| Código del proyecto | MIT |
| ParlaMint 5.0 (incluye ParlaMint-ES) | CC BY 4.0: se puede reutilizar citando la fuente, `http://hdl.handle.net/11356/2004` |
| Qwen3.5-397B-A17B (modelo principal) | Apache 2.0 (confirmar en la ficha oficial del modelo antes de la entrega) |
| gpt-oss-120b (alternativa evaluada) | Apache 2.0 |
| Meta-Llama-3.3-70B | Descartado: licencia propia de Meta, no reconocida como abierta por la OSI |
| Dependencias de Python | Ver `THIRD_PARTY.md` |

### 3.4 Directrices éticas para una IA fiable (UE)

Correspondencia con los siete requisitos de las directrices del grupo de expertos de la Comisión Europea (lista ALTAI):

| Requisito | En el proyecto |
|---|---|
| Acción y supervisión humanas | Anotación humana de referencia; revisión de resultados antes de publicar; la IA no decide sobre personas |
| Solidez técnica y seguridad | Evaluación contra reglas, acuerdo entre anotadoras (kappa 0,71), confirmación en filas nuevas, caché y reanudación ante caídas del proveedor |
| Privacidad y gestión de datos | Minimización, el modelo no recibe identidad, resultados agregados |
| Transparencia | Código, prompts y evaluación abiertos; cada predicción indica si la decidió una regla o el modelo |
| Diversidad, no discriminación y equidad | Error por género medido y reducido; muestreo con igual precisión por género; sin inferencia de género |
| Bienestar social y ambiental | Uso responsable de recursos: reglas cuando bastan, el híbrido ahorra ~27 % de llamadas al modelo, muestra estratificada como alternativa al corpus completo |
| Rendición de cuentas | Repositorio público, decisiones documentadas, limitaciones declaradas |

## 4. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Uso para señalar o clasificar a personas concretas | Solo resultados agregados; sin rankings individuales; documentación del uso previsto |
| Interpretar el tiempo de palabra como influencia | Declararlo como limitación en todos los resultados |
| Atribuir al género lo que se debe al reglamento o al grupo | Controles por tipo de sección, grupo parlamentario y cargo (ministros) |
| Sesgo del modelo de lenguaje | Error por género medido en la evaluación y la confirmación; método híbrido; vigilancia periódica en producción |
| Etiquetas de referencia sesgadas o inconsistentes | Guía de anotación versionada, anotación a ciegas, segunda anotadora y kappa; no se cambian etiquetas para que cuadren con el modelo |
| Género binario en los metadatos | Documentarlo y no inferir género |
| Dependencia de un proveedor externo de IA | API compatible con OpenAI y modelo intercambiable con un parámetro; caché y reanudación; reintentos automáticos; alternativa de modelo autoalojado (la caída de OVHcloud AI Endpoints del 27/10/2026 lo puso a prueba) |
| Datos desactualizados (hasta febrero de 2023) | Declararlo en el README y la presentación; ingesta de datos nuevos en producción |
| Fuga de credenciales | Tokens fuera del repositorio (`.env` y credenciales en `.gitignore`), tokens de alcance limitado y con caducidad, revocación al terminar |

## Fuentes

- Reglamento (UE) 2024/1689 de Inteligencia Artificial, considerando 62 y Anexo III: <https://ai-act-service-desk.ec.europa.eu/en/ai-act/recital-62>
- Reglamento (UE) 2026/1744 («Ómnibus Digital» de IA): <https://natlawreview.com/article/eu-digital-omnibus-ai-enters-force>
- Ficha de ParlaMint 5.0 en CLARIN.SI (licencia CC BY 4.0): <https://www.clarin.si/repository/xmlui/handle/11356/2004?show=full>
- Licencia de Qwen3.5-397B-A17B: <https://apxml.com/models/qwen35-397b-a17b>
