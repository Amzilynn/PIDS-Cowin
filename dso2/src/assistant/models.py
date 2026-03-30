from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ProductRecord:
    url: str
    name: str
    categories: List[str]
    image: str
    indications: str
    form: str
    product_info: str
    product_class: str
    composition: str
    usage_advice: str
    contraindications: str


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    product_name: str
    score: float
    text: str
    metadata: Dict[str, str]
