# Presencia y protagonismo de las mujeres en debates parlamentarios

Sistema de IA abierta que analiza **texto** de debates parlamentarios para cuantificar la presencia de las mujeres y su rol protagonista.

Proyecto del reto **"Mujeres por la IA Abierta"** (SEDIA, Comunidad IA de Código Abierto).

> **Estado:** en desarrollo (octubre 2026). Las secciones marcadas con `TODO` se completan a medida que avanza el proyecto.

## Descripción

TODO: resumen de 3-4 frases una vez definidas las métricas.

Idea general:

1. Se parte de transcripciones parlamentarias con metadatos de orador (corpus ParlaMint).
2. Se calculan métricas de **presencia** (cuánto hablan las mujeres) y de **protagonismo** (qué rol ocupan en el debate: abrir, cerrar, moderar, intervenciones largas, etc.).
3. Se evalúa el sistema contra un conjunto anotado a mano.
4. El diseño es **independiente de la fuente de texto** y **agnóstico respecto al modelo**: si se usa un LLM, se accede mediante una API compatible con OpenAI y puede sustituirse por cualquier modelo abierto.

Detalle de las métricas: [docs/01-metricas.md](docs/01-metricas.md).

## Instalación

```bash
git clone <URL-del-repositorio>
cd presencia-parlamentaria
python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Datos

Los datos **no se incluyen** en el repositorio. Instrucciones de descarga y licencia: [data/README.md](data/README.md) y [docs/02-datos.md](docs/02-datos.md).

## Uso

TODO: ejemplo de ejecución cuando exista el primer prototipo.

## Estructura del repositorio

```
├── README.md          Este archivo
├── LICENSE            Licencia del código
├── THIRD_PARTY.md     Componentes de terceros y sus licencias
├── requirements.txt   Dependencias
├── data/              Datos (no versionados; ver data/README.md)
├── docs/              Métricas, datos, ética y plan de producción
├── src/presencia/     Código fuente
└── tests/             Pruebas
```

## Ética y cumplimiento

Marco ético, riesgos y cumplimiento normativo: [docs/03-etica.md](docs/03-etica.md).

## Componentes de terceros

Ver [THIRD_PARTY.md](THIRD_PARTY.md).

## Hoja de ruta

- [ ] Definir métricas de presencia y protagonismo
- [x] Explorar el corpus y documentar sus límites
- [ ] Prototipo de extracción de métricas
- [ ] Conjunto de evaluación anotado a mano
- [ ] Evaluación y análisis de sesgos
- [ ] Plan de puesta en producción
- [ ] Ampliación a otras fuentes (prensa) mediante adaptadores

## Licencia

Código bajo licencia MIT. Ver [LICENSE](LICENSE). Los datos tienen sus propias licencias (ver THIRD_PARTY.md).
