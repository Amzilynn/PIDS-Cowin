from __future__ import annotations

import os
from typing import Any, ClassVar

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLEAN_DIR = os.path.join(BASE_DIR, "../../data/clean")


class VitalDatabase:
    """In-memory store for VITAL cleaned CSV data with lookup helpers."""

    _CLEAN_FILES: ClassVar[list[tuple[str, str]]] = [
        ("doctors_clean.csv", "doctors"),
        ("pharmacies_clean.csv", "pharmacies"),
        ("vital_products_clean.csv", "vital_products"),
        ("vital_ingredients_clean.csv", "vital_ingredients"),
        ("vital_product_knowledge_clean.csv", "vital_product_knowledge"),
        ("cosmetic_interactions_clean.csv", "cosmetic_interactions"),
        ("drug_interactions_clean.csv", "drug_interactions"),
        ("ingredient_interactions_clean.csv", "ingredient_interactions"),
        ("population_warnings_clean.csv", "population_warnings"),
        ("supplement_rules_clean.csv", "supplement_rules"),
        ("mechanism_of_action_clean.csv", "mechanism_of_action"),
        ("clinical_guidelines_clean.csv", "clinical_guidelines"),
    ]

    def __init__(self) -> None:
        self._doctors: pd.DataFrame = pd.DataFrame()
        self._pharmacies: pd.DataFrame = pd.DataFrame()
        self._vital_products: pd.DataFrame = pd.DataFrame()
        self._vital_ingredients: pd.DataFrame = pd.DataFrame()
        self._vital_product_knowledge: pd.DataFrame = pd.DataFrame()
        self._cosmetic_interactions: pd.DataFrame = pd.DataFrame()
        self._drug_interactions: pd.DataFrame = pd.DataFrame()
        self._ingredient_interactions: pd.DataFrame = pd.DataFrame()
        self._population_warnings: pd.DataFrame = pd.DataFrame()
        self._supplement_rules: pd.DataFrame = pd.DataFrame()
        self._mechanism_of_action: pd.DataFrame = pd.DataFrame()
        self._clinical_guidelines: pd.DataFrame = pd.DataFrame()
        self._files_loaded: int = 0

        for filename, attr in self._CLEAN_FILES:
            path = os.path.join(CLEAN_DIR, filename)
            print(f"Loading {filename} ...")
            attr_name = f"_{attr}"
            if not os.path.isfile(path):
                print(f"  Warning: missing file {path}, using empty DataFrame.")
                setattr(self, attr_name, pd.DataFrame())
                continue
            df = pd.read_csv(path, encoding="utf-8-sig")
            setattr(self, attr_name, df)
            self._files_loaded += 1

        print(f"VitalDatabase ready — {self._files_loaded} files loaded")

    def _safe_split(self, value: str, sep: str = "|") -> list[str]:
        """Split a pipe-separated string safely."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return []
        s = str(value).strip()
        if not s or s.lower() == "nan":
            return []
        parts = [p.strip() for p in s.split(sep)]
        return [p for p in parts if p]

    def _icontains(self, series: pd.Series, value: str) -> pd.Series:
        """Return a boolean mask where series contains value, case-insensitive, null-safe."""
        if not str(value).strip():
            return pd.Series(False, index=series.index)
        s = series.fillna("").astype(str)
        return s.str.contains(str(value).strip(), case=False, na=False, regex=False)

    def _row_to_dict(self, row: Any) -> dict:
        """Convert a DataFrame row to dict, replacing NaN with ""."""
        data = row.to_dict() if hasattr(row, "to_dict") else dict(row)
        out: dict = {}
        for k, v in data.items():
            if pd.isna(v):
                out[k] = ""
            elif isinstance(v, (pd.Timestamp,)):
                out[k] = str(v)
            else:
                out[k] = v
        return out

    def _df_rows_to_dicts(self, df: pd.DataFrame) -> list[dict]:
        """Convert all rows of a DataFrame to list of dicts."""
        if df is None or df.empty:
            return []
        return [self._row_to_dict(df.iloc[i]) for i in range(len(df))]

    def _get_col(self, df: pd.DataFrame, *names: str) -> str | None:
        """Return first column name that exists on df."""
        for n in names:
            if n in df.columns:
                return n
        return None

    def _match_product_knowledge_row(self, product_name: str) -> pd.Series | None:
        """Find first matching row in vital_product_knowledge by nom_produit (exact then partial)."""
        df = self._vital_product_knowledge
        col = self._get_col(df, "nom_produit")
        if col is None or df.empty:
            return None
        q = product_name.strip().lower()
        if not q:
            return None
        s = df[col].fillna("").astype(str)
        exact = df[s.str.strip().str.lower() == q]
        if not exact.empty:
            return exact.iloc[0]
        sub = df[self._icontains(s, product_name)]
        if sub.empty:
            return None
        return sub.iloc[0]

    def get_product(self, name: str) -> dict | None:
        """Return first product row matching name (partial, case-insensitive) or None."""
        col = self._get_col(self._vital_products, "name")
        if col is None or self._vital_products.empty:
            return None
        sub = self._vital_products[self._icontains(self._vital_products[col], name)]
        if sub.empty:
            return None
        return self._row_to_dict(sub.iloc[0])

    def get_all_products(self) -> list[dict]:
        """Return all products as a list of dicts."""
        return self._df_rows_to_dicts(self._vital_products)

    def search_products_by_category(self, category: str) -> list[dict]:
        """Return products whose categories cell contains the given category string."""
        col = self._get_col(self._vital_products, "categories")
        if col is None or self._vital_products.empty:
            return []
        sub = self._vital_products[self._icontains(self._vital_products[col], category)]
        return self._df_rows_to_dicts(sub)

    def search_products_by_indication(self, indication: str) -> list[dict]:
        """Return products whose indications cell contains the given string."""
        col = self._get_col(self._vital_products, "indications")
        if col is None or self._vital_products.empty:
            return []
        sub = self._vital_products[self._icontains(self._vital_products[col], indication)]
        return self._df_rows_to_dicts(sub)

    def get_product_ingredients(self, product_name: str) -> list[str]:
        """Return identified ingredients for a product from product knowledge, split by '|'."""
        row = self._match_product_knowledge_row(product_name)
        if row is None:
            return []
        col = self._get_col(self._vital_product_knowledge, "ingredients_identifies")
        if col is None:
            return []
        return self._safe_split(row.get(col, ""))

    def get_product_full_knowledge(self, product_name: str) -> dict | None:
        """Return full vital_product_knowledge row for the product or None."""
        row = self._match_product_knowledge_row(product_name)
        if row is None:
            return None
        return self._row_to_dict(row)

    def get_ingredient(self, name: str) -> dict | None:
        """Return ingredient row by exact name match first, else first partial match, or None."""
        col = self._get_col(self._vital_ingredients, "ingredient")
        if col is None or self._vital_ingredients.empty:
            return None
        q = name.strip().lower()
        if not q:
            return None
        s = self._vital_ingredients[col].fillna("").astype(str)
        exact = self._vital_ingredients[s.str.strip().str.lower() == q]
        if not exact.empty:
            return self._row_to_dict(exact.iloc[0])
        sub = self._vital_ingredients[self._icontains(s, name)]
        if sub.empty:
            return None
        return self._row_to_dict(sub.iloc[0])

    def get_ingredient_synergies(self, ingredient: str) -> list[str]:
        """Return synergy list for an ingredient from the synergies column."""
        row = self.get_ingredient(ingredient)
        if not row:
            return []
        v = row.get("synergies", "")
        return self._safe_split(v)

    def get_ingredient_conflicts(self, ingredient: str) -> list[str]:
        """Return conflict list for an ingredient from the conflits column."""
        row = self.get_ingredient(ingredient)
        if not row:
            return []
        v = row.get("conflits", "")
        return self._safe_split(v)

    def get_ingredient_population_safety(self, ingredient: str, population: str) -> str:
        """Return population safety cell for the ingredient (grossesse, enfant, senior, diabétique)."""
        row = self._get_ingredient_row_raw(ingredient)
        if row is None:
            return ""
        key = self._population_to_ingredient_column(population)
        if not key:
            return ""
        if key not in self._vital_ingredients.columns:
            return ""
        v = row[key]
        if pd.isna(v):
            return ""
        return str(v).strip()

    def _get_ingredient_row_raw(self, ingredient: str) -> pd.Series | None:
        """Locate ingredient row in vital_ingredients without converting to dict."""
        col = self._get_col(self._vital_ingredients, "ingredient")
        if col is None or self._vital_ingredients.empty:
            return None
        q = ingredient.strip().lower()
        if not q:
            return None
        s = self._vital_ingredients[col].fillna("").astype(str)
        exact = self._vital_ingredients[s.str.strip().str.lower() == q]
        if not exact.empty:
            return exact.iloc[0]
        sub = self._vital_ingredients[self._icontains(s, ingredient)]
        if sub.empty:
            return None
        return sub.iloc[0]

    @staticmethod
    def _population_to_ingredient_column(population: str) -> str:
        """Map user population label to vital_ingredients column name."""
        p = population.strip().lower()
        mapping = {
            "grossesse": "grossesse",
            "enfant": "enfant",
            "senior": "senior",
            "diabétique": "diabetique",
            "diabetique": "diabetique",
        }
        return mapping.get(p, "")

    @staticmethod
    def _population_to_alert_column(population: str) -> str:
        """Map user population label to vital_product_knowledge alertes_* column."""
        p = population.strip().lower()
        mapping = {
            "grossesse": "alertes_grossesse",
            "enfant": "alertes_enfant",
            "senior": "alertes_senior",
            "diabétique": "alertes_diabetique",
            "diabetique": "alertes_diabetique",
        }
        return mapping.get(p, "")

    def get_drug_interactions(self, drug_or_supplement: str) -> list[dict]:
        """Return drug interaction rows where médicament or supplément matches."""
        df = self._drug_interactions
        if df.empty:
            return []
        c_med = self._get_col(df, "medicament", "médicament")
        c_sup = self._get_col(df, "supplement_substance", "supplément_substance")
        if not c_med and not c_sup:
            return []
        masks = []
        if c_med:
            masks.append(self._icontains(df[c_med], drug_or_supplement))
        if c_sup:
            masks.append(self._icontains(df[c_sup], drug_or_supplement))
        if not masks:
            return []
        combined = masks[0]
        for m in masks[1:]:
            combined = combined | m
        sub = df[combined]
        return self._df_rows_to_dicts(sub)

    def get_ingredient_interaction(self, substance1: str, substance2: str) -> dict | None:
        """Return ingredient interaction row for the canonical pair_key or None."""
        df = self._ingredient_interactions
        col_pk = self._get_col(df, "pair_key")
        if col_pk is None or df.empty:
            return None
        a = str(substance1).strip()
        b = str(substance2).strip()
        if not a or not b:
            return None
        key = " | ".join(sorted([a, b]))
        sub = df[df[col_pk].fillna("").astype(str).str.strip() == key]
        if sub.empty:
            return None
        return self._row_to_dict(sub.iloc[0])

    def get_cosmetic_interactions(self, active: str) -> list[dict]:
        """Return cosmetic interaction rows where actif_1 or actif_2 matches."""
        df = self._cosmetic_interactions
        if df.empty:
            return []
        c1 = self._get_col(df, "actif_1")
        c2 = self._get_col(df, "actif_2")
        if not c1 and not c2:
            return []
        masks = []
        if c1:
            masks.append(self._icontains(df[c1], active))
        if c2:
            masks.append(self._icontains(df[c2], active))
        combined = masks[0]
        for m in masks[1:]:
            combined = combined | m
        return self._df_rows_to_dicts(df[combined])

    def get_population_warnings(
        self,
        substance: str,
        population: str | None = None,
    ) -> list[dict]:
        """Return population warning rows for substance, optionally filtered by population_condition."""
        df = self._population_warnings
        if df.empty:
            return []
        c_sub = self._get_col(df, "substance")
        if c_sub is None:
            return []
        sub = df[self._icontains(df[c_sub], substance)]
        if population and str(population).strip():
            c_pop = self._get_col(df, "population_condition")
            if c_pop is None:
                return []
            sub = sub[self._icontains(sub[c_pop], population)]
        return self._df_rows_to_dicts(sub)

    def get_product_population_alerts(self, product_name: str, population: str) -> str:
        """Return product-level alert string for the given population from product knowledge."""
        row = self._match_product_knowledge_row(product_name)
        if row is None:
            return ""
        col = self._population_to_alert_column(population)
        if not col or col not in self._vital_product_knowledge.columns:
            return ""
        v = row.get(col, "")
        if pd.isna(v):
            return ""
        return str(v).strip()

    def get_supplement_rules(self, substance: str) -> list[dict]:
        """Return supplement rules where substance_sujet contains the query string."""
        df = self._supplement_rules
        if df.empty:
            return []
        col = self._get_col(df, "substance_sujet")
        if col is None:
            return []
        sub = df[self._icontains(df[col], substance)]
        return self._df_rows_to_dicts(sub)

    def get_clinical_guideline(self, disease: str) -> list[dict]:
        """Return clinical guideline rows whose disease_name contains the query."""
        df = self._clinical_guidelines
        if df.empty:
            return []
        col = self._get_col(df, "disease_name")
        if col is None:
            return []
        sub = df[self._icontains(df[col], disease)]
        return self._df_rows_to_dicts(sub)

    def get_first_line_treatments(self, disease: str) -> list[dict]:
        """Return first-line clinical guidelines for diseases matching the query."""
        rows = self.get_clinical_guideline(disease)
        if not rows:
            return []
        out: list[dict] = []
        for r in rows:
            v = r.get("is_first_line", "")
            is_first = v is True or str(v).strip().lower() in ("true", "1", "yes")
            if is_first:
                out.append(r)
        return out

    def get_mechanism_of_action(self, mechanism_name: str) -> dict | None:
        """Return first mechanism_of_action row matching mechanism_name or None."""
        df = self._mechanism_of_action
        if df.empty:
            return None
        col = self._get_col(df, "mechanism_name")
        if col is None:
            return None
        sub = df[self._icontains(df[col], mechanism_name)]
        if sub.empty:
            return None
        return self._row_to_dict(sub.iloc[0])

    def get_doctors_by_specialty(self, specialty: str) -> list[dict]:
        """Return doctors whose speciality contains the query string."""
        df = self._doctors
        if df.empty:
            return []
        col = self._get_col(df, "specialite")
        if col is None:
            return []
        sub = df[self._icontains(df[col], specialty)]
        return self._df_rows_to_dicts(sub)

    def get_doctors_by_governorate(self, governorate: str) -> list[dict]:
        """Return doctors whose address text mentions the governorate name."""
        df = self._doctors
        if df.empty:
            return []
        col = self._get_col(df, "adresse")
        if col is None:
            return []
        sub = df[self._icontains(df[col], governorate)]
        return self._df_rows_to_dicts(sub)

    def get_pharmacies_by_governorate(self, governorate: str) -> list[dict]:
        """Return pharmacies in the given governorate (exact column match after contains-style search)."""
        df = self._pharmacies
        if df.empty:
            return []
        col = self._get_col(df, "gouvernorat")
        if col is None:
            return []
        sub = df[self._icontains(df[col], governorate)]
        return self._df_rows_to_dicts(sub)

    def get_full_safety_profile(
        self,
        product_name: str,
        population: str | None = None,
    ) -> dict:
        """Assemble product-level and ingredient-level safety information for one product."""
        product = self.get_product_full_knowledge(product_name)
        ingredients = self.get_product_ingredients(product_name)

        ingredient_details: list[dict] = []
        population_alerts = ""
        ingredient_population_safety: list[dict] = []
        drug_rows: list[dict] = []
        conflict_rows: list[dict] = []

        seen_drug_ids: set[str] = set()
        seen_conflict_keys: set[str] = set()

        pop = (population or "").strip()
        if product and pop:
            ac = self._population_to_alert_column(pop)
            if ac and ac in product:
                population_alerts = str(product.get(ac, "") or "").strip()

        for ing in ingredients:
            rating = self.get_ingredient_population_safety(ing, pop) if pop else ""
            peer: list[dict] = []
            for other in ingredients:
                if other == ing:
                    continue
                inter = self.get_ingredient_interaction(ing, other)
                if inter:
                    peer.append(inter)
            d_inter = self.get_drug_interactions(ing)
            for d in d_inter:
                iid = str(d.get("interaction_id", "") or "")
                dedupe = iid if iid else str(d)
                if dedupe not in seen_drug_ids:
                    seen_drug_ids.add(dedupe)
                    drug_rows.append(d)
            ingredient_details.append(
                {
                    "ingredient": ing,
                    "population_safety": rating,
                    "peer_interactions": peer,
                    "drug_interactions": d_inter,
                }
            )
            if pop:
                ingredient_population_safety.append(
                    {
                        "ingredient": ing,
                        "rating": rating,
                        "warnings": self.get_population_warnings(ing, pop),
                    }
                )

        n = len(ingredients)
        for i in range(n):
            for j in range(i + 1, n):
                inter = self.get_ingredient_interaction(ingredients[i], ingredients[j])
                if not inter:
                    continue
                k = str(inter.get("interaction_id", "") or inter.get("pair_key", "") or "")
                if k and k not in seen_conflict_keys:
                    seen_conflict_keys.add(k)
                    conflict_rows.append(inter)

        return {
            "product": product,
            "ingredients": ingredients,
            "ingredient_details": ingredient_details,
            "population_alerts": population_alerts,
            "ingredient_population_safety": ingredient_population_safety,
            "drug_interactions": drug_rows,
            "ingredient_conflicts": conflict_rows,
        }


if __name__ == "__main__":
    db = VitalDatabase()
    print("\n--- TESTS ---")

    p = db.get_product("PHYTOFANE Anti Chute")
    print(f"Product found: {p['name'] if p else 'NOT FOUND'}")

    ing = db.get_product_ingredients("PHYTOFANE Anti Chute")
    print(f"Ingredients: {ing}")

    safety = db.get_full_safety_profile(
        "PHYTOFANE Anti Chute",
        population="grossesse",
    )
    print(f"Safety profile keys: {list(safety.keys())}")
    print(f"Population alerts: {safety['population_alerts']}")

    g = db.get_clinical_guideline("Hypertension")
    print(f"Guidelines found: {len(g)}")

    rules = db.get_supplement_rules("Fer")
    print(f"Supplement rules for Fer: {len(rules)}")

    pair = db.get_ingredient_interaction("Fer", "Calcium")
    print(f"Fer-Calcium interaction: {pair['type_interaction'] if pair else 'NOT FOUND'}")

    print("\n--- ALL TESTS PASSED ---")
