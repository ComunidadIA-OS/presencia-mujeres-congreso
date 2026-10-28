# Seguridad y datos personales

## Qué notificar

- Vulnerabilidades en el código o en sus dependencias.
- **Credenciales expuestas** (tokens de API, claves) en el repositorio o en su historial.
- **Datos personales publicados por error**: textos de intervenciones, archivos por persona o cualquier dato que permita evaluar a una persona concreta.
- Resultados del sistema que puedan usarse para señalar o perjudicar a una persona.

## Cómo notificarlo

No abras una *issue* pública. Usa la opción **«Report a vulnerability»** de la pestaña *Security* de GitHub (aviso privado) o escribe a las personas responsables del proyecto. Indica qué has encontrado, dónde y, si puedes, cómo reproducirlo.

Responderemos lo antes posible. Si se confirma, corregiremos el problema y, en el caso de datos personales o credenciales, los retiraremos también del historial del repositorio.

## Buenas prácticas del proyecto

- Los tokens se guardan en un archivo `.env` que Git ignora, nunca en el código ni en notebooks.
- Los tokens tienen el alcance mínimo y caducidad, y se revocan al dejar de usarse.
- Los datos en bruto no se versionan; en el repositorio solo hay identificadores, etiquetas y resultados agregados.
- El modelo de IA no recibe nombre, grupo ni género de quien habla.

## Versiones con soporte

Este es un prototipo desarrollado durante un reto. Solo se mantiene la rama `main`.
