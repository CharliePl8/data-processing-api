# DATA-PROCESSING-API

API REST en FastAPI para procesar, validar, limpiar y exportar archivos CSV con soporte para autenticación JWT, vistas previas y análisis básico de datos.

## Características

- Carga de archivos CSV y conversión a JSON.
- Carga múltiple de CSV con resumen consolidado.
- Vista previa de filas con límite configurable.
- Metadatos del archivo: filas, columnas, delimitador, nulos y tamaño.
- Validación de esquema mediante columnas requeridas.
- Normalización de fechas con detección automática o columnas explícitas.
- Informe de calidad de datos.
- Procesamiento por bloques para archivos grandes.
- Exportación a JSON o CSV con selección opcional de columnas.
- Limpieza configurable de espacios en blanco.
- Autenticación JWT para endpoints protegidos.
- Configuración de seguridad y CORS mediante variables de entorno.

## Requisitos

- Python 3.12 o superior.
- Entorno virtual local (.venv).

Paquetes usados:

- `fastapi`
- `uvicorn`
- `pandas`
- `python-multipart`
- `python-jose[cryptography]`
- `pytest`

## Instalación

Si ya tienes el proyecto clonado, activa el entorno virtual e instala las dependencias desde [requirements.txt](requirements.txt):

### Windows

```bash
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

### Bash / Git Bash / WSL

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Ejecutar la API

Desde la raíz del proyecto:

```bash
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

La API quedará disponible en:

- http://127.0.0.1:8000
- Documentación Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Variables de entorno

La API permite ajustar varios parámetros sin modificar el código:

- `MAX_FILE_SIZE_BYTES`
- `RATE_LIMIT_REQUESTS`
- `RATE_LIMIT_WINDOW_SECONDS`
- `CORS_ORIGINS`
- `CORS_METHODS`
- `CORS_HEADERS`
- `CORS_ALLOW_CREDENTIALS`
- `CORS_MAX_AGE`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `API_AUTH_USERNAME`
- `API_AUTH_PASSWORD`

## Autenticación

Los endpoints que procesan CSV requieren un token JWT.

### Obtener token

```bash
curl -X POST "http://127.0.0.1:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secret-password"
```

### Usar el token

```bash
curl -X POST "http://127.0.0.1:8000/preview?limit=5" \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@archivo.csv"
```

## Ejecutar tests

```bash
python -m pytest -q
```

## Estructura del proyecto

- `app/main.py`: inicialización de la API y middlewares.
- `app/api/routes/`: endpoints HTTP de la aplicación.
- `app/services/`: lógica de lectura, validación y transformación de CSV.
- `app/core/`: configuración y seguridad.
- `app/tests/`: pruebas de la API.

## Flujo de autenticación

1. El cliente hace `POST /token` con usuario y contraseña.
2. Si las credenciales son válidas, la API devuelve un JWT.
3. El cliente envía ese token en el header `Authorization: Bearer <TOKEN>`.
4. Los endpoints protegidos validan el token antes de procesar cualquier CSV.

## Endpoints

### `GET /health`

Verifica que la API esté funcionando.

### `POST /token`

Devuelve un JWT si las credenciales son correctas.

Body (form-data):

- `username`
- `password`

### `POST /upload`

Sube un CSV y devuelve su contenido como JSON.

Query params:

- `trim_whitespace`: `true` por defecto.
- `columns`: columnas concretas si se desea filtrar la salida.

### `POST /preview`

Devuelve una vista previa limitada de las primeras filas.

Query params:

- `limit`: número de filas de vista previa. Por defecto, `5`.
- `columns`: columnas concretas a devolver.
- `trim_whitespace`: `true` por defecto.

### `POST /metadata`

Devuelve metadatos del CSV sin exponer todos los datos.

Query params:

- `trim_whitespace`: `true` por defecto.

### `POST /validate-schema`

Valida que el CSV contenga las columnas requeridas.

Query params:

- `required_columns`: lista de columnas requeridas.
- `trim_whitespace`: `true` por defecto.

### `POST /normalize-dates`

Normaliza columnas de fecha a un formato estándar.

Query params:

- `date_columns`: columnas de fecha explícitas. Si no se envían, intenta detectarlas automáticamente.
- `columns`: columnas concretas a devolver.
- `output_format`: formato de salida. Por defecto, `%Y-%m-%d`.
- `trim_whitespace`: `true` por defecto.

### `POST /quality-report`

Genera un informe de calidad de datos.

Query params:

- `columns`: columnas concretas a analizar.
- `trim_whitespace`: `true` por defecto.

### `POST /chunk-summary`

Procesa el CSV por bloques para archivos grandes.

Query params:

- `chunk_size`: tamaño de cada bloque. Por defecto, `1000`.
- `sample_rows`: filas de ejemplo del primer bloque. Por defecto, `5`.
- `columns`: columnas concretas a analizar.
- `trim_whitespace`: `true` por defecto.

### `POST /export-json`

Exporta el CSV como JSON descargable.

Query params:

- `columns`: columnas concretas a exportar.
- `trim_whitespace`: `true` por defecto.

### `POST /export-csv`

Exporta el CSV como archivo CSV descargable.

Query params:

- `columns`: columnas concretas a exportar.
- `trim_whitespace`: `true` por defecto.

### `POST /upload-multiple`

Sube varios CSV y devuelve un resumen consolidado.

Query params:

- `trim_whitespace`: `true` por defecto.

## Ejemplos de uso

### Obtener token

```bash
curl -X POST "http://127.0.0.1:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secret-password"
```

### Subir un archivo

```bash
curl -X POST "http://127.0.0.1:8000/upload" \
  -H "Authorization: Bearer <TOKEN>" \
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

- El proyecto detecta separadores comunes como `;`, `,`, tabulación y `|`.
- Los valores `NULL` y `[NULL]` se tratan como nulos.
- La API valida la estructura básica antes de procesar el archivo.
- El CSV debe tener una fila de cabecera y todas las filas deben mantener la misma cantidad de columnas; si una fila no coincide, la API responderá con un error `400`.
- Para despliegues reales, conviene cambiar `JWT_SECRET_KEY` y las credenciales por defecto mediante variables de entorno.
