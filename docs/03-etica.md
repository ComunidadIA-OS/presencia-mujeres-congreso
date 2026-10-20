# Ética, perspectiva de género y cumplimiento

> **Estado:** borrador inicial. Se completa en paralelo al desarrollo.

## Principios de partida

- **Sin inferencia de género:** se usa el género declarado en los metadatos del corpus; el sistema no lo deduce de nombres o de la voz.
- **Análisis agregado:** mide la representación en conjunto (sesiones, grupos, periodos), no evalúa a personas concretas.
- **Transparencia:** métricas, datos y limitaciones documentados y abiertos.

## Marco normativo a revisar

- RGPD (los oradores son personas con cargo público, pero siguen siendo datos personales).
- Reglamento europeo de IA (AI Act): clasificar el nivel de riesgo del sistema.
- Licencias de los datos y de los modelos usados.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Interpretar el tiempo de palabra como influencia | Declararlo como limitación |
| Género binario en los metadatos | Documentarlo y no inferir género |
| Sesgo del modelo de lenguaje | Evaluación por género sobre muestra anotada a mano |
| Datos desactualizados (hasta 2022) | Declararlo en README y presentación |

## Plan de puesta en producción

TODO: permisos y acuerdos necesarios, base legal, quién usaría el sistema, mantenimiento y monitorización.
