# CSV Reader API

API en FastAPI para cargar, limpiar, inspeccionar y exportar archivos CSV.

## Caracteristicas

- Carga de un CSV y conversion a JSON.
- Carga multiple de CSV con resumen consolidado.
- Vista previa de filas con limite configurable.
- Metadatos del archivo: filas, columnas, delimitador, nulos, tamano.
- Validacion de esquema por columnas requeridas.
- Normalizacion de fechas con deteccion automatica o columnas explicitas.
- Informe de calidad de datos.
- Procesamiento por chunks para archivos grandes.
- Exportacion a JSON o CSV, con seleccion opcional de columnas.
- Limpieza configurable de espacios en blanco.

## Requisitos

- Python 3.12 o superior.
- Entorno virtual local en `.venv`.

Paquetes usados:

- `fastapi`
- `uvicorn`
- `pandas`
- `python-multipart`
- `pytest`

## Instalacion

Si ya tienes el proyecto clonado, activa el entorno virtual e instala las dependencias:

### Windows

```bash
.venv\Scripts\activate
python -m pip install fastapi uvicorn pandas python-multipart pytest
```

### Bash / Git Bash / WSL

```bash
source .venv/bin/activate
python -m pip install fastapi uvicorn pandas python-multipart pytest
```

## Ejecutar la API

Desde la raiz del proyecto:

```bash
/csv_reader/.venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

La API quedara disponible en:

- http://127.0.0.1:8000
- Documentacion Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Ejecutar tests

```bash
python -m pytest app/tests/testCsvApi.py
```

## Endpoints

### `GET /health`

Verifica que la API este funcionando.

### `POST /upload`

Sube un CSV y devuelve su contenido como JSON.

Query params:

- `trim_whitespace` - `true` por defecto.
- `columns` - columnas concretas si se desea filtrar la salida.

### `POST /preview`

Devuelve una vista previa limitada de las primeras filas.

Query params:

- `limit` - numero de filas de vista previa. Por defecto `5`.
- `columns` - columnas concretas a devolver.
- `trim_whitespace` - `true` por defecto.

### `POST /metadata`

Devuelve metadatos del CSV sin exponer todos los datos.

Query params:

- `trim_whitespace` - `true` por defecto.

### `POST /validate-schema`

Valida que el CSV contenga columnas requeridas.

Query params:

- `required_columns` - lista de columnas requeridas.
- `trim_whitespace` - `true` por defecto.

### `POST /normalize-dates`

Normaliza columnas de fecha a un formato estandar.

Query params:

- `date_columns` - columnas de fecha explicitas. Si no se envian, intenta detectarlas automaticamente.
- `columns` - columnas concretas a devolver.
- `output_format` - formato de salida. Por defecto `%Y-%m-%d`.
- `trim_whitespace` - `true` por defecto.

### `POST /quality-report`

Genera un informe de calidad de datos.

Query params:

- `columns` - columnas concretas a analizar.
- `trim_whitespace` - `true` por defecto.

### `POST /chunk-summary`

Procesa el CSV por bloques para archivos grandes.

Query params:

- `chunk_size` - tamano de cada bloque. Por defecto `1000`.
- `sample_rows` - filas de ejemplo del primer bloque. Por defecto `5`.
- `columns` - columnas concretas a analizar.
- `trim_whitespace` - `true` por defecto.

### `POST /export-json`

Exporta el CSV como JSON descargable.

Query params:

- `columns` - columnas concretas a exportar.
- `trim_whitespace` - `true` por defecto.

### `POST /export-csv`

Exporta el CSV como CSV descargable.

Query params:

- `columns` - columnas concretas a exportar.
- `trim_whitespace` - `true` por defecto.

### `POST /upload-multiple`

Sube varios CSV y devuelve un resumen consolidado.

Query params:

- `trim_whitespace` - `true` por defecto.

## Ejemplos de uso

### Subir un archivo

```bash
curl -X POST "http://127.0.0.1:8000/upload" \
  -F "file=@archivo.csv"
```

### Exportar solo columnas concretas

```bash
curl -X POST "http://127.0.0.1:8000/export-csv?columns=name&columns=city" \
  -F "file=@archivo.csv" \
  -o archivo_filtrado.csv
```

### Normalizar fechas indicando columnas

```bash
curl -X POST "http://127.0.0.1:8000/normalize-dates?date_columns=created_at&date_columns=updated_at" \
  -F "file=@archivo.csv"
```

## Notas

- El proyecto detecta separadores comunes como `;`, `,`, tabulacion y `|`.
- Los valores `NULL` y `[NULL]` se tratan como nulos.
- La API valida estructura basica antes de procesar el archivo.
