# Componentes de terceros y licencias

El código de este proyecto se publica bajo licencia MIT (ver `LICENSE`). Usa los siguientes componentes de terceros, cada uno con su propia licencia, compatibles con ese uso.

## Datos

| Componente | Uso | Licencia | Fuente |
|---|---|---|---|
| ParlaMint-ES 5.0 (dentro de *Multilingual comparable corpora of parliamentary debates ParlaMint 5.0*) | Transcripciones y metadatos de los debates del Congreso, 2015–2023 | CC BY 4.0 | <http://hdl.handle.net/11356/2004> |

Los datos **no se redistribuyen** en el repositorio: se descargan de su fuente oficial (ver `data/README.md`). El repositorio incluye identificadores de intervención, etiquetas anotadas por el equipo, respuestas del modelo y resultados agregados derivados del corpus, con atribución a ParlaMint.

## Modelos de lenguaje

Se usan mediante OVHcloud AI Endpoints (API compatible con OpenAI). El proyecto no redistribuye sus pesos.

| Modelo | Uso | Licencia |
|---|---|---|
| Qwen3.5-397B-A17B | Modelo principal del método híbrido | Apache 2.0 |
| gpt-oss-120b | Comparación | Apache 2.0 |
| Qwen3.5-9B | Comparación (no completada) | Apache 2.0 |

Se descartó Meta-Llama-3.3-70B por tener una licencia propia no reconocida como abierta por la OSI.

## Dependencias de Python

| Paquete | Uso | Licencia |
|---|---|---|
| pandas | Tratamiento de tablas | BSD-3-Clause |
| lxml | Lectura de XML | BSD-3-Clause |
| openai | Cliente compatible con la API de OVHcloud AI Endpoints | Apache 2.0 |
| matplotlib | Gráficos (`figures.py`, `app.py`) | Licencia de Matplotlib (basada en PSF, compatible con BSD) |
| gradio | Demo (`app.py`) | Apache 2.0 |
| pytest | Pruebas | MIT |

El resto del código usa solo la biblioteca estándar de Python (licencia PSF).

## Servicios

| Servicio | Uso |
|---|---|
| OVHcloud AI Endpoints | Inferencia de los modelos durante el reto, sujeta a sus condiciones de uso |
| OVHcloud AI Notebooks (JupyterLab) | Entorno de ejecución de la clasificación del corpus |

## Documentación

`CODE_OF_CONDUCT.md` se basa en el Contributor Covenant 2.1 (CC BY 4.0).
