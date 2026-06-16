from pydantic import BaseModel
from typing import List, Dict, Any

class CSVResponse(BaseModel):
	file_name: str
	rows: int
	columns: List[str]
	data: List[Dict[str, Any]]