import csv
import io
from typing import List

import pandas as pd
from fastapi import HTTPException, UploadFile, status

from app.core.config import (
	DEFAULT_DELIMITER,
	DEFAULT_OUTPUT_DATE_FORMAT,
	DEFAULT_ENCODING,
	DELIMITER_CANDIDATES,
	DATE_DETECTION_MIN_PARSE_RATE,
	DATE_DETECTION_SAMPLE_SIZE,
	MAX_FILE_SIZE_BYTES,
	NULL_VALUES,
)


# DEF: _normalize_cell_value: Normaliza una celda individual aplicando trim opcional y convirtiendo marcadores de nulo a None.
def _normalize_cell_value(value, trim_whitespace: bool = True):
	if pd.isna(value):
		return None

	if isinstance(value, str):
		normalized_value = value.strip() if trim_whitespace else value
		if trim_whitespace and normalized_value == "":
			return None
		if normalized_value in NULL_VALUES:
			return None
		return normalized_value

	return value


# DEF: _build_clean_dataframe: Aplica limpieza configurable al DataFrame para normalizar textos, encabezados y nulos.
def _build_clean_dataframe(df: pd.DataFrame, trim_whitespace: bool = True):
	cleaned_df = df.copy().astype(object)

	if trim_whitespace:
		cleaned_df.columns = [
			column.strip() if isinstance(column, str) else column
			for column in cleaned_df.columns
		]

	for column in cleaned_df.columns:
		cleaned_df[column] = cleaned_df[column].map(
			lambda value: _normalize_cell_value(value, trim_whitespace)
		)

	# Convertir NaN remanentes a None para que la respuesta final sea JSON serializable.
	return cleaned_df.where(pd.notna(cleaned_df), None)


# DEF: _filter_dataframe_columns: Conserva únicamente las columnas solicitadas y valida que existan en el CSV.
def _filter_dataframe_columns(df: pd.DataFrame, selected_columns: List[str]):
	missing_columns = [column for column in selected_columns if column not in df.columns]
	if missing_columns:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"Las columnas solicitadas no existen en el archivo: {', '.join(missing_columns)}.",
		)

	return df.loc[:, selected_columns]


# DEF: _detect_date_columns: Detecta columnas que parecen contener fechas usando una muestra de valores no nulos.
def _detect_date_columns(
	df: pd.DataFrame,
	sample_size: int = DATE_DETECTION_SAMPLE_SIZE,
	min_parse_rate: float = DATE_DETECTION_MIN_PARSE_RATE,
):
	detected_columns = []

	for column in df.columns:
		series = df[column].dropna()
		if series.empty:
			continue

		sample = series.head(sample_size)
		parsed_sample = pd.to_datetime(sample, errors="coerce", format="mixed", dayfirst=True)
		parse_rate = parsed_sample.notna().mean()
		if parse_rate >= min_parse_rate and parsed_sample.notna().any():
			detected_columns.append(column)

	return detected_columns


# DEF: _normalize_date_columns: Convierte columnas de fecha a un formato homogéneo y reporta las filas que no se pudieron interpretar.
def _normalize_date_columns(
	df: pd.DataFrame,
	date_columns: List[str],
	output_format: str = DEFAULT_OUTPUT_DATE_FORMAT,
):
	normalized_df = df.copy()
	normalized_columns = []
	failure_report = {}

	for column in date_columns:
		if column not in normalized_df.columns:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail=f"La columna de fecha '{column}' no existe en el archivo.",
			)

		parsed_series = pd.to_datetime(
			normalized_df[column],
			errors="coerce",
			format="mixed",
			dayfirst=True,
		)
		parse_failures = int(normalized_df[column].notna().sum() - parsed_series.notna().sum())
		try:
			normalized_values = parsed_series.dt.strftime(output_format)
		except ValueError as exc:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail=f"El formato de salida '{output_format}' no es válido.",
			) from exc

		normalized_df[column] = normalized_values.where(parsed_series.notna(), None)
		normalized_columns.append(column)
		failure_report[column] = parse_failures

	return normalized_df, normalized_columns, failure_report


# DEF: _build_quality_report: Genera un informe de calidad básico con nulos, duplicados y columnas vacías.
def _build_quality_report(df: pd.DataFrame):
	total_rows = len(df)
	total_columns = len(list(df.columns))
	null_counts = df.isna().sum()
	null_percentages = {
		column: round((int(count) / total_rows) * 100, 2) if total_rows else 0.0
		for column, count in null_counts.items()
	}
	empty_columns = [column for column, count in null_counts.items() if int(count) == total_rows and total_rows > 0]
	duplicated_rows = int(df.duplicated().sum())
	duplicate_percentage = round((duplicated_rows / total_rows) * 100, 2) if total_rows else 0.0
	rows_with_nulls = int(df.isna().any(axis=1).sum())

	return {
		"rows": total_rows,
		"columns": total_columns,
		"duplicated_rows": duplicated_rows,
		"duplicate_percentage": duplicate_percentage,
		"rows_with_nulls": rows_with_nulls,
		"null_counts": {column: int(count) for column, count in null_counts.items()},
		"null_percentages": null_percentages,
		"empty_columns": empty_columns,
		"column_dtypes": {column: str(dtype) for column, dtype in df.dtypes.items()},
	}


# DEF: _prepare_csv_content: Lee y valida el CSV, devolviendo el contenido limpio y el separador detectado sin construir un DataFrame completo.
def _prepare_csv_content(file: UploadFile, trim_whitespace: bool = True):
	# Intentar determinar el tamaño sin cargar todo en memoria usando seek.
	raw_bytes = None
	try:
		file.file.seek(0, io.SEEK_END)
		size = file.file.tell()
		file.file.seek(0)
	except (AttributeError, OSError):
		# Si no es seekable, leer para medir tamaño (fallback).
		raw_bytes = file.file.read()
		size = len(raw_bytes)
		file.file.seek(0)

	# Validar que el archivo no esté vacío.
	if size == 0:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"El archivo '{file.filename}' está vacío.",
		)

	# Validar que el archivo no supere el tamaño máximo permitido.
	if size > MAX_FILE_SIZE_BYTES:
		raise HTTPException(
			status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
			detail=f"El archivo '{file.filename}' supera el tamaño máximo permitido.",
		)

	# Si no leímos el contenido antes (seek OK), leer ahora para procesarlo.
	if raw_bytes is None:
		raw_bytes = file.file.read()
		file.file.seek(0)  # Reiniciar el puntero del archivo para futuras lecturas

	# Intentar decodificar el contenido del archivo usando la codificación predeterminada y manejar errores de decodificación.
	try:
		raw_content = raw_bytes.decode(DEFAULT_ENCODING)
	except UnicodeDecodeError as exc:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"No se pudo decodificar el archivo '{file.filename}' con {DEFAULT_ENCODING}.",
		) from exc

	# Normalizar espacios externos; si queda vacío, no hay nada útil que procesar.
	raw_content = raw_content.strip()
	if not raw_content:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"El archivo '{file.filename}' no contiene contenido útil.",
		)

	# Algunas exportaciones envuelven cada línea entre comillas; si ocurre, las quitamos antes de analizar.
	lines = raw_content.splitlines()
	if lines and all(
		(line.startswith('"') and line.endswith('"'))
		or (line.startswith("'") and line.endswith("'"))
		for line in lines
		if line.strip()
	):
		raw_content = "\n".join(line[1:-1] for line in lines)

	# Intentar detectar el delimitador real del archivo; si falla, usamos el valor por defecto.
	separator = DEFAULT_DELIMITER
	try:
		separator = csv.Sniffer().sniff(
			raw_content,
			delimiters=list(DELIMITER_CANDIDATES),
		).delimiter
	except csv.Error:
		pass

	# Validar la estructura antes de devolver el contenido para procesamiento posterior.
	rows = [
		row
		for row in csv.reader(io.StringIO(raw_content), delimiter=separator)
		if any(cell.strip() for cell in row)
	]
	if not rows:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"El archivo '{file.filename}' no tiene filas válidas.",
		)

	expected_columns = len(rows[0])
	if expected_columns == 0:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"El archivo '{file.filename}' no tiene columnas válidas.",
		)

	for row_number, row in enumerate(rows[1:], start=2):
		if len(row) != expected_columns:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail=(
					f"El archivo '{file.filename}' tiene una estructura CSV inconsistente en la fila {row_number}."
				),
			)

	return {
		"file_name": file.filename,
		"file_size_bytes": len(raw_bytes),
		"separator": separator,
		"raw_content": raw_content,
	}


# DEF: _prepare_csv_dataframe: Valida, detecta y carga el CSV una sola vez para reutilizar el mismo flujo en todos los endpoints.
def _prepare_csv_dataframe(file: UploadFile, trim_whitespace: bool = True):
	prepared_content = _prepare_csv_content(file, trim_whitespace)

	# Leer el CSV con pandas ya validado, usando el separador detectado y tratando marcadores de nulo.
	try:
		df = pd.read_csv(
			io.StringIO(prepared_content["raw_content"]),
			sep=prepared_content["separator"],
			na_values=list(NULL_VALUES),
			keep_default_na=True,
		)
	except pd.errors.ParserError as exc:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"El archivo '{file.filename}' no tiene un formato CSV válido.",
		) from exc

	if df.empty and len(df.columns) == 0:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"El archivo '{file.filename}' no tiene filas ni columnas válidas.",
		)

	return {
		"file_name": prepared_content["file_name"],
		"file_size_bytes": prepared_content["file_size_bytes"],
		"separator": prepared_content["separator"],
		"dataframe": df,
	}


# DEF: read_csv_file: Función que recibe un archivo CSV, lo procesa y devuelve un diccionario con el nombre del archivo, número de filas, número de columnas, delimitador detectado y los datos en formato de lista de diccionarios.
async def read_csv_file(
	file: UploadFile,
	trim_whitespace: bool = True,
	selected_columns: List[str] | None = None,
):
	# Reutilizar el mismo flujo base para lectura, validación y limpieza.
	prepared_csv = _prepare_csv_dataframe(file, trim_whitespace)
	clean_df = _build_clean_dataframe(prepared_csv["dataframe"], trim_whitespace)
	if selected_columns:
		clean_df = _filter_dataframe_columns(clean_df, selected_columns)
	null_cells = int(clean_df.isna().sum().sum())

	return {
		"file_name": prepared_csv["file_name"],
		"file_size_bytes": prepared_csv["file_size_bytes"],
		"rows": len(clean_df),
		"columns": len(list(clean_df.columns)),
		"delimiter": prepared_csv["separator"],
		"cleaning": {
			"trim_whitespace": trim_whitespace,
		},
		"selected_columns": selected_columns,
		"null_cells": null_cells,
		"data": clean_df.to_dict(orient="records"),
	}


# DEF: export_csv_file: Devuelve el contenido CSV listo para descarga, permitiendo filtrar columnas concretas.
async def export_csv_file(
	file: UploadFile,
	columns: List[str] | None = None,
	trim_whitespace: bool = True,
):
	prepared_csv = _prepare_csv_dataframe(file, trim_whitespace)
	clean_df = _build_clean_dataframe(prepared_csv["dataframe"], trim_whitespace)
	selected_columns = columns or None

	if selected_columns:
		clean_df = _filter_dataframe_columns(clean_df, selected_columns)

	csv_buffer = io.StringIO()
	clean_df.to_csv(csv_buffer, index=False, lineterminator="\n")

	return {
		"file_name": prepared_csv["file_name"],
		"file_size_bytes": prepared_csv["file_size_bytes"],
		"delimiter": prepared_csv["separator"],
		"selected_columns": selected_columns,
		"csv_content": csv_buffer.getvalue(),
	}


# DEF: preview_csv_file: Devuelve una muestra de las primeras filas del CSV sin perder los metadatos principales.
async def preview_csv_file(
	file: UploadFile,
	limit: int = 5,
	trim_whitespace: bool = True,
	selected_columns: List[str] | None = None,
):
	prepared_csv = _prepare_csv_dataframe(file, trim_whitespace)
	clean_df = _build_clean_dataframe(prepared_csv["dataframe"], trim_whitespace)
	if selected_columns:
		clean_df = _filter_dataframe_columns(clean_df, selected_columns)
	preview_df = clean_df.head(limit)

	return {
		"file_name": prepared_csv["file_name"],
		"file_size_bytes": prepared_csv["file_size_bytes"],
		"rows": len(clean_df),
		"preview_rows": len(preview_df),
		"columns": len(list(clean_df.columns)),
		"delimiter": prepared_csv["separator"],
		"cleaning": {
			"trim_whitespace": trim_whitespace,
		},
		"selected_columns": selected_columns,
		"data": preview_df.to_dict(orient="records"),
	}


# DEF: get_csv_metadata: Devuelve información estructural del archivo sin exponer los datos completos.
async def get_csv_metadata(file: UploadFile, trim_whitespace: bool = True):
	prepared_csv = _prepare_csv_dataframe(file, trim_whitespace)
	clean_df = _build_clean_dataframe(prepared_csv["dataframe"], trim_whitespace)

	return {
		"file_name": prepared_csv["file_name"],
		"file_size_bytes": prepared_csv["file_size_bytes"],
		"rows": len(clean_df),
		"columns": len(list(clean_df.columns)),
		"delimiter": prepared_csv["separator"],
		"column_names": list(clean_df.columns),
		"null_cells": int(clean_df.isna().sum().sum()),
		"cleaning": {
			"trim_whitespace": trim_whitespace,
		},
	}


# DEF: validate_csv_schema: Compara las columnas del CSV contra un esquema esperado y devuelve el resultado de la validación.
async def validate_csv_schema(
	file: UploadFile,
	required_columns: List[str],
	trim_whitespace: bool = True,
):
	prepared_csv = _prepare_csv_dataframe(file, trim_whitespace)
	clean_df = _build_clean_dataframe(prepared_csv["dataframe"], trim_whitespace)
	column_names = list(clean_df.columns)
	required_set = set(required_columns)
	present_set = set(column_names)

	missing_columns = [column for column in required_columns if column not in present_set]
	extra_columns = [column for column in column_names if column not in required_set]

	return {
		"file_name": prepared_csv["file_name"],
		"rows": len(clean_df),
		"columns": len(column_names),
		"delimiter": prepared_csv["separator"],
		"required_columns": required_columns,
		"column_names": column_names,
		"missing_columns": missing_columns,
		"extra_columns": extra_columns,
		"valid": len(missing_columns) == 0,
		"cleaning": {
			"trim_whitespace": trim_whitespace,
		},
	}


# DEF: normalize_csv_dates: Normaliza columnas de fecha y, si no se indican, intenta detectarlas automáticamente.
async def normalize_csv_dates(
	file: UploadFile,
	date_columns: List[str] | None = None,
	selected_columns: List[str] | None = None,
	trim_whitespace: bool = True,
	output_format: str = DEFAULT_OUTPUT_DATE_FORMAT,
):
	prepared_csv = _prepare_csv_dataframe(file, trim_whitespace)
	clean_df = _build_clean_dataframe(prepared_csv["dataframe"], trim_whitespace)

	resolved_date_columns = date_columns or _detect_date_columns(clean_df)
	normalized_df, normalized_columns, failure_report = _normalize_date_columns(
		clean_df,
		resolved_date_columns,
		output_format=output_format,
	)

	if selected_columns:
		normalized_df = _filter_dataframe_columns(normalized_df, selected_columns)

	return {
		"file_name": prepared_csv["file_name"],
		"file_size_bytes": prepared_csv["file_size_bytes"],
		"rows": len(normalized_df),
		"columns": len(list(normalized_df.columns)),
		"delimiter": prepared_csv["separator"],
		"output_format": output_format,
		"detected_date_columns": _detect_date_columns(clean_df) if date_columns is None else [],
		"date_columns": resolved_date_columns,
		"normalized_date_columns": normalized_columns,
		"date_parse_failures": failure_report,
		"selected_columns": selected_columns,
		"cleaning": {
			"trim_whitespace": trim_whitespace,
		},
		"data": normalized_df.to_dict(orient="records"),
	}


# DEF: get_csv_quality_report: Genera un informe de calidad con métricas útiles para archivos CSV grandes o sucios.
async def get_csv_quality_report(
	file: UploadFile,
	trim_whitespace: bool = True,
	selected_columns: List[str] | None = None,
):
	prepared_csv = _prepare_csv_dataframe(file, trim_whitespace)
	clean_df = _build_clean_dataframe(prepared_csv["dataframe"], trim_whitespace)
	if selected_columns:
		clean_df = _filter_dataframe_columns(clean_df, selected_columns)

	report = _build_quality_report(clean_df)

	return {
		"file_name": prepared_csv["file_name"],
		"file_size_bytes": prepared_csv["file_size_bytes"],
		"delimiter": prepared_csv["separator"],
		"selected_columns": selected_columns,
		"cleaning": {
			"trim_whitespace": trim_whitespace,
		},
		"report": report,
	}


# DEF: get_csv_chunk_summary: Procesa el CSV por bloques y devuelve un resumen pensado para archivos grandes.
async def get_csv_chunk_summary(
	file: UploadFile,
	chunk_size: int = 1000,
	sample_rows: int = 5,
	trim_whitespace: bool = True,
	selected_columns: List[str] | None = None,
):
	prepared_content = _prepare_csv_content(file, trim_whitespace)

	try:
		chunk_reader = pd.read_csv(
			io.StringIO(prepared_content["raw_content"]),
			sep=prepared_content["separator"],
			na_values=list(NULL_VALUES),
			keep_default_na=True,
			chunksize=chunk_size,
		)
	except pd.errors.ParserError as exc:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"El archivo '{prepared_content['file_name']}' no tiene un formato CSV válido.",
		) from exc

	chunk_summaries = []
	total_rows = 0
	total_null_cells = 0
	first_chunk_sample = []
	columns_in_result = []

	for chunk_index, chunk in enumerate(chunk_reader, start=1):
		clean_chunk = _build_clean_dataframe(chunk, trim_whitespace)
		if selected_columns:
			clean_chunk = _filter_dataframe_columns(clean_chunk, selected_columns)

		chunk_rows = len(clean_chunk)
		chunk_null_cells = int(clean_chunk.isna().sum().sum())
		total_rows += chunk_rows
		total_null_cells += chunk_null_cells
		columns_in_result = list(clean_chunk.columns)

		if not first_chunk_sample:
			first_chunk_sample = clean_chunk.head(sample_rows).to_dict(orient="records")

		chunk_summaries.append(
			{
				"chunk_index": chunk_index,
				"rows": chunk_rows,
				"null_cells": chunk_null_cells,
			}
		)

	return {
		"file_name": prepared_content["file_name"],
		"file_size_bytes": prepared_content["file_size_bytes"],
		"delimiter": prepared_content["separator"],
		"chunk_size": chunk_size,
		"chunks_count": len(chunk_summaries),
		"total_rows": total_rows,
		"total_null_cells": total_null_cells,
		"selected_columns": selected_columns,
		"columns": columns_in_result,
		"sample_rows": sample_rows,
		"first_chunk_sample": first_chunk_sample,
		"chunks": chunk_summaries,
		"cleaning": {
			"trim_whitespace": trim_whitespace,
		},
	}


# DEF: read_multiple_csv_files: Función que recibe una lista de archivos CSV, llama a read_csv_file para cada uno de ellos y devuelve una lista con los resultados.
async def read_multiple_csv_files(files: List[UploadFile], trim_whitespace: bool = True):
	# Reutilizar la lógica de un solo archivo para mantener una única ruta de validación y limpieza.
	results = []
	for file in files:
		result = await read_csv_file(file, trim_whitespace=trim_whitespace)
		results.append(result)

	summary = {
		"files_count": len(results),
		"total_rows": sum(result["rows"] for result in results),
		"total_columns": sum(result["columns"] for result in results),
		"delimiters": sorted({result["delimiter"] for result in results}),
	}

	return {
		"summary": summary,
		"files": results,
	}
