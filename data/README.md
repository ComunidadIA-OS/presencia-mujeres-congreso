# Datos

Esta carpeta no contiene datos versionados. Los corpus se descargan desde su fuente original para respetar sus licencias y no redistribuirlos.

## ParlaMint-ES 5.0

- **Fuente:** CLARIN.SI, <http://hdl.handle.net/11356/2004>
- **Archivo:** `ParlaMint-ES.tgz` (aprox. 84 MB)
- **MD5 (según la ficha):** `2ba1216f3fcf1300ee74f50efe42ec6a`
- **Licencia (según la ficha):** CC BY 4.0. Pendiente de confirmar en la página del repositorio.
- **Contenido:** sesiones plenarias del Congreso de los Diputados, del 01/01/2015 al 23/02/2023.

### Descarga y verificación

```bash
mkdir -p data/raw && cd data/raw
curl -L -o ParlaMint-ES.tgz "https://www.clarin.si/repository/xmlui/bitstream/handle/11356/2004/ParlaMint-ES.tgz?sequence=8&isAllowed=y"
md5sum ParlaMint-ES.tgz        # En Mac: md5 ParlaMint-ES.tgz
tar -xzf ParlaMint-ES.tgz
```

### Estructura tras descomprimir

```
data/raw/
├── README-ES               Descripción oficial del corpus
├── ParlaMint-ES.txt/       Versión en texto plano (la que usamos)
│   ├── 00README
│   ├── 2015/ ... 2023/     Una carpeta por año
└── ParlaMint-ES.TEI/       Versión XML (reserva)
```

### Formato de la versión de texto

- Cada archivo `.txt` tiene dos columnas separadas por tabulador: **ID de la intervención** y **texto**.
- Los comentarios del transcriptor (aplausos, interrupciones...) van entre dobles corchetes.
- Cada archivo `.txt` tiene asociados dos archivos TSV de metadatos: uno con nombres de columna en español y otro en inglés.

### Cita

Citar el recurso por su identificador: <http://hdl.handle.net/11356/2004>.

## Reproducibilidad

TODO: añadir un script en `src/presencia/` que verifique el MD5 y la versión de los datos.
