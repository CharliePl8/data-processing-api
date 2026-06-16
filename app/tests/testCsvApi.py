from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# Test cases para la carga de un archivo CSV válido
def test_upload_csv():
	csv_content = "name;age\nAlice;30\nBob;25"
	files = {
		"file": ("test.csv", csv_content, "text/csv")
		}
	
	response = client.post("/upload", files=files)
	
	# Verificar que la respuesta sea correcta y que los datos se hayan procesado como se espera
	assert response.status_code == 200
	data = response.json()
	assert data["file_name"] == "test.csv"
	assert data["delimiter"] == ";"
	assert data["rows"] == 2
	assert data["columns"] == 2
	assert data["data"] == [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]


# Test cases para la limpieza configurable de espacios por defecto
def test_upload_csv_trims_whitespace_by_default():
	csv_content = " name ; city \n Alice ; Madrid \n Bob ; Barcelona "
	files = {"file": ("trimmed.csv", csv_content, "text/csv")}

	response = client.post("/upload", files=files)

	assert response.status_code == 200
	data = response.json()
	assert data["data"] == [
		{"name": "Alice", "city": "Madrid"},
		{"name": "Bob", "city": "Barcelona"},
	]


# Test cases para desactivar la limpieza de espacios cuando el cliente lo solicita
def test_upload_csv_can_disable_whitespace_trimming():
	csv_content = " name ; city \n Alice ; Madrid \n"
	files = {"file": ("raw-spaces.csv", csv_content, "text/csv")}

	response = client.post("/upload?trim_whitespace=false", files=files)

	assert response.status_code == 200
	data = response.json()
	assert data["data"] == [{"name ": " Alice ", " city ": " Madrid"}]


# Test cases para la vista previa del CSV
def test_preview_csv_returns_limited_rows():
	csv_content = "name;age\nAlice;30\nBob;25\nMarta;40"
	files = {"file": ("preview.csv", csv_content, "text/csv")}

	response = client.post("/preview?limit=2", files=files)

	assert response.status_code == 200
	data = response.json()
	assert data["rows"] == 3
	assert data["preview_rows"] == 2
	assert data["data"] == [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
	assert data["selected_columns"] is None


# Test cases para la vista previa filtrando columnas concretas
def test_preview_csv_can_select_columns():
	csv_content = "name;age;city\nAlice;30;Madrid\nBob;25;Sevilla\nMarta;40;Valencia"
	files = {"file": ("preview-filtered.csv", csv_content, "text/csv")}

	response = client.post("/preview?limit=2&columns=name&columns=city", files=files)

	assert response.status_code == 200
	data = response.json()
	assert data["selected_columns"] == ["name", "city"]
	assert data["preview_rows"] == 2
	assert data["data"] == [{"name": "Alice", "city": "Madrid"}, {"name": "Bob", "city": "Sevilla"}]


# Test cases para la vista previa cuando se solicita una columna inexistente
def test_preview_csv_missing_column_returns_400():
	csv_content = "name;age\nAlice;30\nBob;25"
	files = {"file": ("preview-missing.csv", csv_content, "text/csv")}

	response = client.post("/preview?columns=name&columns=city", files=files)

	assert response.status_code == 400
	assert "no existen" in response.json()["detail"]


# Test cases para los metadatos del CSV
def test_metadata_csv_returns_summary_information():
	csv_content = "name;age\nAlice;30\nBob;[NULL]"
	files = {"file": ("metadata.csv", csv_content, "text/csv")}

	response = client.post("/metadata", files=files)

	assert response.status_code == 200
	data = response.json()
	assert data["file_name"] == "metadata.csv"
	assert data["rows"] == 2
	assert data["columns"] == 2
	assert data["delimiter"] == ";"
	assert data["column_names"] == ["name", "age"]
	assert data["null_cells"] == 1


# Test cases para exportar el CSV como JSON descargable
def test_export_json_csv_returns_attachment():
	csv_content = "name;age\nAlice;30\nBob;25"
	files = {"file": ("export.csv", csv_content, "text/csv")}

	response = client.post("/export-json", files=files)

	assert response.status_code == 200
	assert response.headers["content-disposition"] == 'attachment; filename="export.csv.json"'
	data = response.json()
	assert data["file_name"] == "export.csv"
	assert data["rows"] == 2
	assert data["data"] == [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
	assert data["selected_columns"] is None


# Test cases para exportar solo columnas concretas
def test_export_json_csv_can_select_columns():
	csv_content = "name;age;city\nAlice;30;Madrid\nBob;25;Sevilla"
	files = {"file": ("filtered.csv", csv_content, "text/csv")}

	response = client.post("/export-json?columns=name&columns=city", files=files)

	assert response.status_code == 200
	data = response.json()
	assert data["selected_columns"] == ["name", "city"]
	assert data["data"] == [
		{"name": "Alice", "city": "Madrid"},
		{"name": "Bob", "city": "Sevilla"},
	]


# Test cases para el error cuando se solicita una columna que no existe
def test_export_json_csv_missing_column_returns_400():
	csv_content = "name;age\nAlice;30\nBob;25"
	files = {"file": ("missing-column.csv", csv_content, "text/csv")}

	response = client.post("/export-json?columns=name&columns=city", files=files)

	assert response.status_code == 400
	assert "no existen" in response.json()["detail"]


# Test cases para exportar el CSV como archivo descargable
def test_export_csv_returns_attachment():
	csv_content = "name;age\nAlice;30\nBob;25"
	files = {"file": ("export.csv", csv_content, "text/csv")}

	response = client.post("/export-csv", files=files)

	assert response.status_code == 200
	assert response.headers["content-disposition"] == 'attachment; filename="export.csv.clean.csv"'
	assert response.text.strip() == "name,age\nAlice,30\nBob,25"


# Test cases para exportar solo columnas concretas en CSV
def test_export_csv_can_select_columns():
	csv_content = "name;age;city\nAlice;30;Madrid\nBob;25;Sevilla"
	files = {"file": ("filtered.csv", csv_content, "text/csv")}

	response = client.post("/export-csv?columns=name&columns=city", files=files)

	assert response.status_code == 200
	assert response.headers["content-disposition"] == 'attachment; filename="filtered.csv.filtered.csv"'
	assert response.text.strip() == "name,city\nAlice,Madrid\nBob,Sevilla"


# Test cases para validar un esquema de columnas mínimas
def test_validate_schema_csv_reports_missing_and_extra_columns():
	csv_content = "name;age;city\nAlice;30;Madrid\nBob;25;Sevilla"
	files = {"file": ("schema.csv", csv_content, "text/csv")}

	response = client.post(
		"/validate-schema?required_columns=name&required_columns=age&required_columns=country",
		files=files,
	)

	assert response.status_code == 200
	data = response.json()
	assert data["file_name"] == "schema.csv"
	assert data["required_columns"] == ["name", "age", "country"]
	assert data["missing_columns"] == ["country"]
	assert data["extra_columns"] == ["city"]
	assert data["valid"] is False


# Test cases para normalizar columnas de fecha indicadas explícitamente
def test_normalize_dates_csv_with_explicit_columns():
	csv_content = "name;created_at\nAlice;12/06/2026\nBob;2026-06-13"
	files = {"file": ("dates.csv", csv_content, "text/csv")}

	response = client.post("/normalize-dates?date_columns=created_at", files=files)

	assert response.status_code == 200
	data = response.json()
	assert data["date_columns"] == ["created_at"]
	assert data["normalized_date_columns"] == ["created_at"]
	assert data["data"] == [
		{"name": "Alice", "created_at": "2026-06-12"},
		{"name": "Bob", "created_at": "2026-06-13"},
	]


# Test cases para autodetectar columnas de fecha
def test_normalize_dates_csv_auto_detects_date_columns():
	csv_content = "name;created_at\nAlice;12/06/2026\nBob;13/06/2026"
	files = {"file": ("auto-dates.csv", csv_content, "text/csv")}

	response = client.post("/normalize-dates", files=files)

	assert response.status_code == 200
	data = response.json()
	assert data["date_columns"] == ["created_at"]
	assert data["detected_date_columns"] == ["created_at"]
	assert data["data"] == [
		{"name": "Alice", "created_at": "2026-06-12"},
		{"name": "Bob", "created_at": "2026-06-13"},
	]


# Test cases para el informe de calidad de datos
def test_quality_report_csv_returns_metrics():
	csv_content = "name;age;empty\nAlice;30;\nBob;[NULL];\nAlice;30;"
	files = {"file": ("quality.csv", csv_content, "text/csv")}

	response = client.post("/quality-report", files=files)

	assert response.status_code == 200
	data = response.json()
	assert data["file_name"] == "quality.csv"
	assert data["report"]["duplicated_rows"] == 1
	assert data["report"]["empty_columns"] == ["empty"]
	assert data["report"]["null_counts"]["age"] == 1
	assert data["report"]["null_counts"]["empty"] == 3


# Test cases para resumir archivos grandes por chunks
def test_chunk_summary_csv_returns_chunk_metrics():
	csv_content = "name;age\nAlice;30\nBob;25\nMarta;40\nLuis;20\nEva;18"
	files = {"file": ("chunks.csv", csv_content, "text/csv")}

	response = client.post("/chunk-summary?chunk_size=2&sample_rows=1", files=files)

	assert response.status_code == 200
	data = response.json()
	assert data["file_name"] == "chunks.csv"
	assert data["chunks_count"] == 3
	assert data["total_rows"] == 5
	assert [chunk["rows"] for chunk in data["chunks"]] == [2, 2, 1]
	assert data["first_chunk_sample"] == [{"name": "Alice", "age": 30}]
	assert data["sample_rows"] == 1


# Test cases para resumir archivos grandes por chunks filtrando columnas
def test_chunk_summary_csv_can_select_columns():
	csv_content = "name;age;city\nAlice;30;Madrid\nBob;25;Sevilla\nMarta;40;Valencia"
	files = {"file": ("chunks-filtered.csv", csv_content, "text/csv")}

	response = client.post("/chunk-summary?chunk_size=2&columns=name&columns=city", files=files)

	assert response.status_code == 200
	data = response.json()
	assert data["selected_columns"] == ["name", "city"]
	assert data["columns"] == ["name", "city"]
	assert data["first_chunk_sample"] == [{"name": "Alice", "city": "Madrid"}, {"name": "Bob", "city": "Sevilla"}]


# Test cases para la normalización de marcadores de nulo
def test_upload_csv_handles_null_markers():
	csv_content = "name;age\nAlice;[NULL]\nBob;NULL"
	files = {"file": ("nulls.csv", csv_content, "text/csv")}

	response = client.post("/upload", files=files)

	assert response.status_code == 200
	data = response.json()
	assert data["data"] == [{"name": "Alice", "age": None}, {"name": "Bob", "age": None}]


# Test cases para la carga de múltiples archivos CSV con resumen consolidado
def test_upload_multiple_csv():
	files = [
		("files", ("first.csv", "x;y\n1;2\n", "text/csv")),
		("files", ("second.csv", "x,y\n3,4\n", "text/csv")),
	]

	response = client.post("/upload-multiple", files=files)

	assert response.status_code == 200
	data = response.json()
	assert data["summary"]["files_count"] == 2
	assert data["summary"]["total_rows"] == 2
	assert data["summary"]["delimiters"] == [",", ";"]
	assert len(data["files"]) == 2
	assert data["files"][0]["file_name"] == "first.csv"
	assert data["files"][0]["delimiter"] == ";"
	assert data["files"][1]["file_name"] == "second.csv"
	assert data["files"][1]["delimiter"] == ","


# Test cases para la carga de un archivo CSV vacío o con formato inválido
def test_upload_empty_csv_returns_400():
	files = {"file": ("empty.csv", "", "text/csv")}

	response = client.post("/upload", files=files)

	assert response.status_code == 400
	assert "vacío" in response.json()["detail"]


# Test cases para la carga de un archivo CSV con estructura inconsistente
def test_upload_invalid_csv_returns_400():
	csv_content = "name;age\nAlice;30;extra\n"
	files = {"file": ("invalid.csv", csv_content, "text/csv")}

	response = client.post("/upload", files=files)

	assert response.status_code == 400
	assert "estructura CSV inconsistente" in response.json()["detail"]