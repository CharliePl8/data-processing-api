from typing import List

import json

from fastapi import APIRouter, File, Query, Response, UploadFile

from app.services.csv_service import (
	get_csv_metadata,
	export_csv_file,
	preview_csv_file,
	read_csv_file,
	read_multiple_csv_files,
	normalize_csv_dates,
	get_csv_quality_report,
	get_csv_chunk_summary,
	validate_csv_schema,
)

router = APIRouter()

# Endpoint para verificar el estado de la API
@router.get("/health")
async def health_check():
	return "healthy"


# Endpoint para subir un archivo CSV y convertirlo a JSON
@router.post("/upload")
async def upload_csv(file: UploadFile = File(...), trim_whitespace: bool = Query(True)):
	return await read_csv_file(file, trim_whitespace=trim_whitespace)


# Endpoint para obtener una vista previa de las primeras filas del CSV
@router.post("/preview")
async def preview_csv(
	file: UploadFile = File(...),
	limit: int = Query(5, ge=1, le=1000),
	columns: List[str] | None = Query(None),
	trim_whitespace: bool = Query(True),
):
	return await preview_csv_file(
		file,
		limit=limit,
		trim_whitespace=trim_whitespace,
		selected_columns=columns,
	)


# Endpoint para obtener metadatos del CSV sin devolver todos los datos
@router.post("/metadata")
async def metadata_csv(file: UploadFile = File(...), trim_whitespace: bool = Query(True)):
	return await get_csv_metadata(file, trim_whitespace=trim_whitespace)


# Endpoint para normalizar columnas de fecha
@router.post("/normalize-dates")
async def normalize_dates_csv(
	file: UploadFile = File(...),
	date_columns: List[str] | None = Query(None),
	columns: List[str] | None = Query(None),
	output_format: str = Query("%Y-%m-%d"),
	trim_whitespace: bool = Query(True),
):
	return await normalize_csv_dates(
		file,
		date_columns=date_columns,
		selected_columns=columns,
		trim_whitespace=trim_whitespace,
		output_format=output_format,
	)


# Endpoint para generar un informe de calidad de datos
@router.post("/quality-report")
async def quality_report_csv(
	file: UploadFile = File(...),
	columns: List[str] | None = Query(None),
	trim_whitespace: bool = Query(True),
):
	return await get_csv_quality_report(
		file,
		trim_whitespace=trim_whitespace,
		selected_columns=columns,
	)


# Endpoint para procesar archivos grandes por chunks
@router.post("/chunk-summary")
async def chunk_summary_csv(
	file: UploadFile = File(...),
	chunk_size: int = Query(1000, ge=1, le=100000),
	sample_rows: int = Query(5, ge=1, le=1000),
	columns: List[str] | None = Query(None),
	trim_whitespace: bool = Query(True),
):
	return await get_csv_chunk_summary(
		file,
		chunk_size=chunk_size,
		sample_rows=sample_rows,
		trim_whitespace=trim_whitespace,
		selected_columns=columns,
	)


# Endpoint para exportar el CSV como JSON descargable
@router.post("/export-json")
async def export_json_csv(
	file: UploadFile = File(...),
	columns: List[str] | None = Query(None),
	trim_whitespace: bool = Query(True),
):
	result = await read_csv_file(
		file,
		trim_whitespace=trim_whitespace,
		selected_columns=columns,
	)
	export_name = f"{result['file_name']}.json"
	content = json.dumps(result, ensure_ascii=False, indent=2)
	return Response(
		content=content,
		media_type="application/json",
		headers={"Content-Disposition": f'attachment; filename="{export_name}"'},
	)


# Endpoint para exportar el CSV como archivo CSV descargable
@router.post("/export-csv")
async def export_csv(
	file: UploadFile = File(...),
	columns: List[str] | None = Query(None),
	trim_whitespace: bool = Query(True),
):
	result = await export_csv_file(
		file,
		columns=columns,
		trim_whitespace=trim_whitespace,
	)
	export_suffix = "filtered" if result["selected_columns"] else "clean"
	export_name = f"{file.filename}.{export_suffix}.csv"
	return Response(
		content=result["csv_content"],
		media_type="text/csv",
		headers={"Content-Disposition": f'attachment; filename="{export_name}"'},
	)


# Endpoint para validar que el CSV contenga un esquema mínimo de columnas requeridas
@router.post("/validate-schema")
async def validate_schema_csv(
	file: UploadFile = File(...),
	required_columns: List[str] = Query(...),
	trim_whitespace: bool = Query(True),
):
	return await validate_csv_schema(
		file,
		required_columns=required_columns,
		trim_whitespace=trim_whitespace,
	)


# Endpoint para subir múltiples archivos CSV y convertirlos a JSON
@router.post("/upload-multiple")
async def upload_multiple_csv(files: List[UploadFile] = File(...), trim_whitespace: bool = Query(True)):
	return await read_multiple_csv_files(files, trim_whitespace=trim_whitespace)