"""Tool functions for VitalAgent (VitalDatabase + VitalRetriever)."""

from __future__ import annotations

import os
import sys
from typing import Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "..")
sys.path.insert(0, SRC_DIR)

from product_knowledge.database import VitalDatabase
from product_knowledge.retriever import VitalRetriever

_db = VitalDatabase()
_retriever = VitalRetriever()


def _product_name_key(p: dict) -> str:
    """Return a lowercase key for deduplication."""
    name = (
        p.get("name")
        or p.get("nom_produit")
        or (p.get("metadata") or {}).get("product_name")
        or ""
    )
    return str(name).strip().lower()


def _normalize_population_for_warnings(population: str) -> str:
    """Map loose population label to metadata value used in Chroma."""
    p = (population or "").strip().lower()
    mapping = {
        "grossesse": "Grossesse",
        "enceinte": "Grossesse",
        "enfant": "Enfant",
        "bébé": "Enfant",
        "bebe": "Enfant",
        "senior": "Senior",
        "diabétique": "Diabétique",
        "diabetique": "Diabétique",
    }
    return mapping.get(p, population.strip() if population else "")


def search_products_by_symptom(query: str) -> dict:
    """Search Vital products relevant to a symptom or condition described in natural language."""
    try:
        sem = _retriever.search_products(str(query), n_results=5)
        exact = _db.search_products_by_indication(str(query))
        seen: dict[str, dict] = {}
        for p in exact:
            k = _product_name_key(p)
            if k:
                seen[k] = p
        for r in sem:
            meta = r.get("metadata") or {}
            name = str(meta.get("product_name", "")).strip()
            k = name.lower()
            if k and k not in seen:
                seen[k] = {
                    "name": name,
                    "indications": (r.get("text") or "")[:800],
                    "source": "semantic_search",
                }
        merged = list(seen.values())
        return {"products": merged, "count": len(merged)}
    except Exception as exc:
        return {"error": str(exc), "products": [], "count": 0}


def get_product_details(product_name: str) -> dict:
    """Get complete details for a specific Vital product by name."""
    try:
        pk = _db.get_product_full_knowledge(product_name)
        if pk:
            return {"product": pk, "found": True}
        p = _db.get_product(product_name)
        if p:
            return {"product": p, "found": True}
        return {"product": None, "found": False}
    except Exception as exc:
        return {"error": str(exc), "product": None, "found": False}


def check_product_safety(product_name: str, population: str = "") -> dict:
    """Check safety profile of a product for a specific population (grossesse, enfant, senior, diabétique)."""
    try:
        pop = str(population).strip() or None
        safety = _db.get_full_safety_profile(product_name, population=pop)
        return {
            "safety": safety,
            "product_name": str(product_name),
            "population": str(population or ""),
        }
    except Exception as exc:
        return {
            "error": str(exc),
            "safety": {},
            "product_name": str(product_name),
            "population": str(population or ""),
        }


def get_ingredient_info(ingredient_name: str) -> dict:
    """Get detailed information about an ingredient including synergies and conflicts."""
    try:
        ing = _db.get_ingredient(ingredient_name)
        syn = _db.get_ingredient_synergies(ingredient_name)
        con = _db.get_ingredient_conflicts(ingredient_name)
        return {
            "ingredient": ing,
            "synergies": syn,
            "conflicts": con,
            "found": ing is not None,
        }
    except Exception as exc:
        return {
            "error": str(exc),
            "ingredient": None,
            "synergies": [],
            "conflicts": [],
            "found": False,
        }


def check_drug_interaction(substance: str) -> dict:
    """Check known drug/supplement interactions involving a substance."""
    try:
        inter = _db.get_drug_interactions(substance)
        return {"interactions": inter, "substance": str(substance), "count": len(inter)}
    except Exception as exc:
        return {"error": str(exc), "interactions": [], "substance": str(substance), "count": 0}


def recommend_products_for_condition(condition: str, population: str = "") -> dict:
    """Recommend Vital products for a condition, optionally with population-specific warnings."""
    try:
        products = _retriever.search_products(str(condition), n_results=5)
        guidelines = _retriever.search_guidelines(str(condition), n_results=3)
        warnings: list[dict[str, Any]] = []
        pop = str(population).strip()
        if pop:
            filt = _normalize_population_for_warnings(pop)
            warnings = _retriever.search_warnings(
                str(condition),
                population=filt if filt else pop,
                n_results=3,
            )
        return {
            "products": products,
            "guidelines": guidelines,
            "warnings": warnings,
            "condition": str(condition),
        }
    except Exception as exc:
        return {
            "error": str(exc),
            "products": [],
            "guidelines": [],
            "warnings": [],
            "condition": str(condition),
        }


def get_clinical_context(disease: str) -> dict:
    """Get clinical guidelines and first-line treatment context for a disease."""
    try:
        g = _db.get_clinical_guideline(disease)
        fl = _db.get_first_line_treatments(disease)
        return {"guidelines": g, "first_line": fl, "disease": str(disease)}
    except Exception as exc:
        return {"error": str(exc), "guidelines": [], "first_line": [], "disease": str(disease)}


def get_supplement_timing_rules(substance: str) -> dict:
    """Get supplement timing and dosage rules for a substance."""
    try:
        rules = _db.get_supplement_rules(substance)
        return {"rules": rules, "substance": str(substance)}
    except Exception as exc:
        return {"error": str(exc), "rules": [], "substance": str(substance)}


_TOOL_FUNCS: dict[str, Any] = {
    "search_products_by_symptom": search_products_by_symptom,
    "get_product_details": get_product_details,
    "check_product_safety": check_product_safety,
    "get_ingredient_info": get_ingredient_info,
    "check_drug_interaction": check_drug_interaction,
    "recommend_products_for_condition": recommend_products_for_condition,
    "get_clinical_context": get_clinical_context,
    "get_supplement_timing_rules": get_supplement_timing_rules,
}


def dispatch_tool(name: str, args: dict[str, Any] | None) -> dict:
    """Invoke a tool by name with a dict of arguments; never raises."""
    fn = _TOOL_FUNCS.get(name)
    if not fn:
        return {"error": f"Tool {name} not found"}
    args = args or {}
    try:
        return fn(**args)
    except Exception as exc:
        return {"error": str(exc)}


TOOLS_SCHEMA: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_products_by_symptom",
            "description": search_products_by_symptom.__doc__ or "",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Symptôme ou pathologie en langage naturel",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_details",
            "description": get_product_details.__doc__ or "",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "Nom du produit VITAL",
                    }
                },
                "required": ["product_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_product_safety",
            "description": check_product_safety.__doc__ or "",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string", "description": "Nom du produit"},
                    "population": {
                        "type": "string",
                        "description": "grossesse, enfant, senior, diabétique, ou vide",
                    },
                },
                "required": ["product_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_ingredient_info",
            "description": get_ingredient_info.__doc__ or "",
            "parameters": {
                "type": "object",
                "properties": {
                    "ingredient_name": {
                        "type": "string",
                        "description": "Nom de l'ingrédient",
                    }
                },
                "required": ["ingredient_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_drug_interaction",
            "description": check_drug_interaction.__doc__ or "",
            "parameters": {
                "type": "object",
                "properties": {
                    "substance": {
                        "type": "string",
                        "description": "Médicament ou substance à vérifier",
                    }
                },
                "required": ["substance"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_products_for_condition",
            "description": recommend_products_for_condition.__doc__ or "",
            "parameters": {
                "type": "object",
                "properties": {
                    "condition": {
                        "type": "string",
                        "description": "Condition médicale ou symptômes",
                    },
                    "population": {
                        "type": "string",
                        "description": "Population optionnelle (ex. Grossesse)",
                    },
                },
                "required": ["condition"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_clinical_context",
            "description": get_clinical_context.__doc__ or "",
            "parameters": {
                "type": "object",
                "properties": {
                    "disease": {
                        "type": "string",
                        "description": "Maladie ou indication clinique",
                    }
                },
                "required": ["disease"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_supplement_timing_rules",
            "description": get_supplement_timing_rules.__doc__ or "",
            "parameters": {
                "type": "object",
                "properties": {
                    "substance": {
                        "type": "string",
                        "description": "Substance ou complément",
                    }
                },
                "required": ["substance"],
            },
        },
    },
]
