# Cómo contribuir

¡Gracias por tu interés! Este proyecto mide la presencia y el protagonismo de las mujeres en debates parlamentarios con IA abierta, y cualquier ayuda es bienvenida: código, datos anotados, documentación o revisión de resultados.

Al participar aceptas el [código de conducta](CODE_OF_CONDUCT.md).

## Ideas para contribuir

- **Más anotación humana**, a ciegas y siguiendo [la guía](docs/04-guia-anotacion.md): es lo que más mejora la fiabilidad de las cifras de calidad.
- **Nuevas métricas:** interrupciones dadas y recibidas, menciones a mujeres en el discurso, apertura y cierre por iniciativa.
- **Otras fuentes:** otros parlamentos de ParlaMint (mismo formato) o transcripciones de audio, mediante adaptadores.
- **Otros modelos abiertos:** el cliente usa una API compatible con OpenAI; cualquier modelo nuevo debe evaluarse con `evaluate.py`, incluido su error por género.
- **Documentación y accesibilidad** de la demo.

## Flujo de trabajo

1. Abre una *issue* describiendo el cambio, salvo que sea una corrección pequeña.
2. Crea una rama desde `main` con un nombre descriptivo (por ejemplo, `metrica-interrupciones`).
3. Instala el entorno y comprueba que los tests pasan:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   python -m pytest -q
   ```
4. Haz commits pequeños con mensajes claros en castellano, que expliquen el qué y el porqué.
5. Abre un *pull request* hacia `main`. La integración continua ejecuta los tests automáticamente.

## Normas del código

- Python 3.11 o superior. Los scripts se ejecutan desde la raíz: `python src/presencia/<script>.py`.
- **Cada función nueva lleva su test** en `tests/`. Los tests no deben depender de los datos reales ni de la API: usa datos inventados mínimos (ver los tests existentes).
- **Preferencia por la biblioteca estándar.** Si añades una dependencia, anótala en `requirements.txt` y su licencia en `THIRD_PARTY.md`, y comprueba que es compatible con la licencia MIT.
- Docstrings y comentarios en castellano.

## Normas sobre datos, privacidad y ética

Son obligatorias, porque el proyecto trata datos personales de cargos públicos:

- **Nunca subas los datos en bruto** de ParlaMint (`data/raw/`): se descargan de la fuente oficial.
- **No subas textos de intervenciones ni archivos por persona.** En el repositorio solo van identificadores de intervención, etiquetas y resultados agregados.
- **No infieras el género** de nadie: usa solo el declarado en los metadatos.
- **No publiques rankings ni evaluaciones de personas concretas.**
- **Nunca subas credenciales** (`.env`, tokens). Si ocurre por error, sigue [SECURITY.md](SECURITY.md).
- **No cambies etiquetas humanas** para que coincidan con el modelo: si una etiqueta parece errónea, documenta la duda y pide una segunda anotación a ciegas.
- Todo cambio en el clasificador debe informar del **error por género**, no solo del acierto global.

## Dudas

Abre una *issue* con la etiqueta `pregunta`.
