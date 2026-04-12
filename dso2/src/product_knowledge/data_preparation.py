import os
import re
import unicodedata
from typing import Dict, List, Tuple

import chardet
import pandas as pd


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "../../data/raw")
CLEAN_DIR = os.path.join(BASE_DIR, "../../data/clean")

EMPTY_MARKERS = {"", "nan", "none", "n/a", "na", "-", "—"}

VALID_GOVERNORATES = {
    "Ariana",
    "Béja",
    "Ben Arous",
    "Bizerte",
    "Gabès",
    "Gafsa",
    "Jendouba",
    "Kairouan",
    "Kasserine",
    "Kébili",
    "Le Kef",
    "Mahdia",
    "La Manouba",
    "Médenine",
    "Monastir",
    "Nabeul",
    "Sfax",
    "Sidi Bouzid",
    "Siliana",
    "Sousse",
    "Tataouine",
    "Tozeur",
    "Tunis",
    "Zaghouan",
}


def normalize_key(text: str) -> str:
    if text is None:
        return ""
    text = str(text).strip().lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    cols = []
    for c in df.columns:
        c2 = normalize_key(c)
        cols.append(c2)
    df.columns = cols
    return df


def detect_file_encoding(path: str) -> str:
    with open(path, "rb") as f:
        raw = f.read(200000)
    detected = chardet.detect(raw).get("encoding")
    return detected or "utf-8"


def try_read_csv(path: str) -> Tuple[pd.DataFrame, str]:
    _ = detect_file_encoding(path)
    encodings = ["utf-8", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            return pd.read_csv(path, encoding=enc, on_bad_lines="warn"), enc
        except Exception:
            continue
    raise ValueError(f"Failed to load CSV with supported encodings: {path}")


def compact_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_text_value(value) -> str:
    if pd.isna(value):
        return ""
    s = str(value)
    s = s.replace("\ufeff", "")
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"https?://\S+", " ", s)
    for bad in ["â€¢", "â€˘", "•", "�?�", "�?", "·"]:
        s = s.replace(bad, " | ")
    s = s.replace("�??", "'").replace("l�", "l'")
    s = s.replace("d�", "d'")
    s = s.replace("�", " ")
    s = compact_spaces(s)
    s = re.sub(r"\s*\|\s*", " | ", s)
    s = s.strip(" |")
    if s.lower() in EMPTY_MARKERS:
        return ""
    return s


def smart_title(s: str) -> str:
    if not s:
        return ""
    parts = re.split(r"(\s+|-|')", s.lower())
    out = []
    for p in parts:
        if p.strip() and p not in {"-", "'"} and not p.isspace():
            out.append(p[0].upper() + p[1:])
        else:
            out.append(p)
    return "".join(out)


def normalize_phone(phone: str) -> str:
    if not phone:
        return ""
    original_plus = "+" if str(phone).strip().startswith("+") else ""
    digits = re.sub(r"[^0-9]", "", str(phone))
    if not digits:
        return ""
    if digits.startswith("216"):
        digits = digits[3:]
    if len(digits) >= 8:
        digits = digits[-8:]
        return f"{original_plus or '+'}216{digits}"
    return ""


def normalize_email(email: str) -> str:
    email = clean_text_value(email).lower()
    if not email:
        return ""
    if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return email
    return ""


def split_clean_join(value: str, separators: str = r"\|") -> str:
    value = clean_text_value(value)
    if not value:
        return ""
    parts = [compact_spaces(x) for x in re.split(separators, value) if compact_spaces(x)]
    return " | ".join(dict.fromkeys(parts))


def split_comma_clean(value: str) -> str:
    value = clean_text_value(value)
    if not value:
        return ""
    parts = [compact_spaces(x) for x in value.split(",") if compact_spaces(x)]
    return ", ".join(dict.fromkeys(parts))


def normalize_enum(value: str, mapping: Dict[str, str], default: str = "") -> str:
    value = clean_text_value(value)
    if not value:
        return default
    key = normalize_key(value)
    return mapping.get(key, default if default != "" else value)


def preprocess_common(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    stats = {"encoding_fixes": 0, "empty_rows_removed": 0, "duplicates_removed": 0}
    df = clean_column_names(df.copy())
    for col in df.columns:
        before = df[col].astype(str).str.count(r"[�â€¢]").sum()
        df[col] = df[col].map(clean_text_value)
        after = df[col].astype(str).str.count(r"[�â€¢]").sum()
        stats["encoding_fixes"] += max(0, int(before - after))
    before = len(df)
    df = df.replace({None: "", pd.NA: ""})
    all_empty = (df.apply(lambda x: x.astype(str).str.strip()).replace("nan", "") == "").all(axis=1)
    df = df.loc[~all_empty].copy()
    stats["empty_rows_removed"] = before - len(df)
    before = len(df)
    df = df.drop_duplicates()
    stats["duplicates_removed"] = before - len(df)
    return df, stats


def process_doctors(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], List[str]]:
    warnings: List[str] = []
    issues = ["telephone", "email", "specialite", "latitude", "longitude"]
    for col in ["nom", "prenom"]:
        if col in df:
            df[col] = df[col].map(smart_title)
    if "telephone" in df:
        df["telephone"] = df["telephone"].map(normalize_phone)
    if "email" in df:
        df["email"] = df["email"].map(normalize_email)
    specialite_map = {
        "mg": "Médecine générale",
        "medecine_generale": "Médecine générale",
        "specialiste_en_medecine_de_famille": "Médecine générale",
    }
    if "specialite" in df:
        df["specialite"] = df["specialite"].map(lambda x: normalize_enum(x, specialite_map, clean_text_value(x)))
    for c in ["latitude", "longitude"]:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if {"latitude", "longitude"}.issubset(df.columns):
        before = len(df)
        df = df[df["latitude"].notna() & df["longitude"].notna()].copy()
        dropped = before - len(df)
        if dropped:
            warnings.append(f"Dropped {dropped} rows with invalid latitude/longitude.")
    if {"prenom", "nom"}.issubset(df.columns):
        df["full_name"] = (df["prenom"].fillna("") + " " + df["nom"].fillna("")).map(compact_spaces)
    return df, warnings, issues


def process_pharmacies(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], List[str]]:
    warnings: List[str] = []
    issues = ["telephone", "type", "gouvernorat", "url", "nom"]
    if "nom" in df:
        df["nom"] = df["nom"].map(smart_title)
    if "telephone" in df:
        df["telephone"] = df["telephone"].map(normalize_phone)
    type_map = {
        "jour": "jour",
        "nuit": "nuit",
        "jour_nuit": "jour/nuit",
        "jour_et_nuit": "jour/nuit",
    }
    if "type" in df:
        df["type"] = df["type"].map(lambda x: normalize_enum(x, type_map, ""))
    gov_map = {normalize_key(g): g for g in VALID_GOVERNORATES}
    if "gouvernorat" in df:
        df["gouvernorat"] = df["gouvernorat"].map(lambda x: normalize_enum(x, gov_map, ""))
        unknown = (df["gouvernorat"] == "").sum()
        if unknown:
            warnings.append(f"{unknown} rows have invalid or missing gouvernorat.")
    if "url" in df:
        df["url_valid"] = df["url"].map(lambda x: bool(re.match(r"^https://", str(x).strip(), re.I)))
    return df, warnings, issues


def process_vital_products(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], List[str]]:
    warnings: List[str] = []
    issues = ["categories", "indications", "compositions", "contre_indications", "forme", "classe"]
    if "name" in df:
        df["name"] = df["name"].map(smart_title)
    if "categories" in df:
        df["categories"] = df["categories"].map(split_comma_clean)
    for col in ["indications", "compositions", "contre_indications", "conseils_d_utilisation"]:
        if col in df:
            df[col] = df[col].map(lambda x: split_clean_join(str(x), separators=r"\||,"))
    forme_map = {
        "gelules": "Gélules",
        "capsules": "Capsules",
        "comprimes": "Comprimés",
        "sirop": "Sirop",
        "spray": "Spray",
        "creme": "Crème",
        "gel": "Gel",
        "huile": "Huile",
        "poudre": "Poudre",
        "ampoules": "Ampoules",
    }
    if "forme" in df:
        df["forme"] = df["forme"].map(lambda x: normalize_enum(x, forme_map, ""))
    classe_map = {
        "complement_alimentaire": "Complément alimentaire",
        "soin": "Soin",
        "soin_capillaire": "Soin Capillaire",
        "medicament": "Médicament",
    }
    if "classe" in df:
        df["classe"] = df["classe"].map(lambda x: normalize_enum(x, classe_map, ""))
    comp_col = "compositions" if "compositions" in df else "compositions_brut"
    advice_col = "conseils_d_utilisation"
    df["has_composition"] = df.get(comp_col, "").astype(str).str.strip().ne("")
    df["has_usage_advice"] = df.get(advice_col, "").astype(str).str.strip().ne("")
    return df, warnings, issues


def process_vital_ingredients(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], List[str]]:
    warnings: List[str] = []
    issues = ["synergies", "conflits", "noms_alternatifs", "grossesse", "enfant", "senior", "diabetique"]
    for col in ["ingredient", "categorie", "role"]:
        if col in df:
            df[col] = df[col].map(clean_text_value)
    for col in ["synergies", "conflits", "noms_alternatifs"]:
        if col in df:
            df[col] = df[col].map(lambda x: split_clean_join(x, separators=r"\||,"))
    status_map = {
        "recommande": "Recommandé",
        "adapte": "Adapté",
        "attention": "Attention",
        "contre_indique": "Contre-indiqué",
        "ci": "Contre-indiqué",
        "essentiel": "Essentiel",
    }
    for col in ["grossesse", "enfant", "senior", "diabetique"]:
        if col in df:
            df[col] = df[col].map(lambda x: normalize_enum(x, status_map, ""))
    return df, warnings, issues


def process_vital_product_knowledge(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], List[str]]:
    warnings: List[str] = []
    issues = [
        "categories",
        "classe",
        "forme",
        "indications",
        "compositions_brut",
        "ingredients_identifies",
        "ingredients_inconnus",
        "interactions_medicamenteuses",
    ]
    if "nom_produit" in df:
        df["nom_produit"] = df["nom_produit"].map(smart_title)
    if "categories" in df:
        df["categories"] = df["categories"].map(split_comma_clean)
    for col in [
        "indications",
        "compositions_brut",
        "ingredients_identifies",
        "ingredients_inconnus",
        "conseils_d_utilisation",
        "contre_indications_produit",
        "interactions_medicamenteuses",
        "alertes_grossesse",
        "alertes_enfant",
        "alertes_senior",
        "alertes_diabetique",
    ]:
        if col in df:
            df[col] = df[col].map(lambda x: split_clean_join(x, separators=r"\||,"))
    return df, warnings, issues


def add_sequential_id(df: pd.DataFrame, prefix: str, col: str) -> pd.DataFrame:
    df = df.reset_index(drop=True).copy()
    df[col] = [f"{prefix}_{i:04d}" for i in range(1, len(df) + 1)]
    return df


def process_cosmetic_interactions(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], List[str]]:
    type_map = {
        "synergie": "SYNERGIE",
        "conflit": "CONFLIT",
        "conflit_modere": "CONFLIT MODÉRÉ",
        "neutre": "NEUTRE",
    }
    if "type_interaction" in df:
        df["type_interaction"] = df["type_interaction"].map(lambda x: normalize_enum(x, type_map, ""))
    df = add_sequential_id(df, "COSM", "interaction_id")
    return df, [], ["type_interaction"]


def process_drug_interactions(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], List[str]]:
    type_map = {
        "antagonisme": "ANTAGONISME",
        "potentialisation": "POTENTIALISATION",
        "reduction_efficacite": "RÉDUCTION EFFICACITÉ",
        "synergie": "SYNERGIE",
        "neutre": "NEUTRE",
    }
    sev_map = {"haute": "haute", "moderee": "modérée", "faible": "faible"}
    if "type_interaction" in df:
        df["type_interaction"] = df["type_interaction"].map(lambda x: normalize_enum(x, type_map, ""))
    if "severite" in df:
        df["severite"] = df["severite"].map(lambda x: normalize_enum(x, sev_map, ""))
    df = add_sequential_id(df, "DRUG", "interaction_id")
    return df, [], ["type_interaction", "severite"]


def process_ingredient_interactions(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], List[str]]:
    type_map = {"synergie": "SYNERGIE", "conflit": "CONFLIT", "neutre": "NEUTRE"}
    if "type_interaction" in df:
        df["type_interaction"] = df["type_interaction"].map(lambda x: normalize_enum(x, type_map, ""))
    if {"substance_1", "substance_2"}.issubset(df.columns):
        df["pair_key"] = df.apply(
            lambda r: " | ".join(sorted([clean_text_value(r["substance_1"]), clean_text_value(r["substance_2"])])),
            axis=1,
        )
    df = add_sequential_id(df, "ING", "interaction_id")
    return df, [], ["type_interaction", "pair_key"]


def process_population_warnings(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], List[str]]:
    pop_map = {
        "grossesse": "Grossesse",
        "enfant": "Enfant",
        "senior": "Senior",
        "diabetique": "Diabétique",
        "insuffisance_renale": "Insuffisance rénale",
        "insuffisance_hepatique": "Insuffisance hépatique",
    }
    alert_map = {
        "contre_indique": "CONTRE-INDIQUÉ",
        "essentiel": "ESSENTIEL",
        "necessaire": "NÉCESSAIRE",
        "recommande": "RECOMMANDÉ",
        "deconseille": "DÉCONSEILLÉ",
        "attention": "ATTENTION",
    }
    sev_map = {"haute": "haute", "moderee": "modérée", "faible": "faible"}
    if "population_condition" in df:
        df["population_condition"] = df["population_condition"].map(lambda x: normalize_enum(x, pop_map, ""))
    if "type_alerte" in df:
        df["type_alerte"] = df["type_alerte"].map(lambda x: normalize_enum(x, alert_map, ""))
    if "severite" in df:
        df["severite"] = df["severite"].map(lambda x: normalize_enum(x, sev_map, ""))
    df = add_sequential_id(df, "WARN", "warning_id")
    return df, [], ["population_condition", "type_alerte", "severite"]


def process_supplement_rules(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], List[str]]:
    cat_map = {"timing": "TIMING", "dosage": "DOSAGE", "association": "ASSOCIATION", "forme": "FORME"}
    imp_map = {"haute": "haute", "moderee": "modérée", "faible": "faible"}
    if "categorie" in df:
        df["categorie"] = df["categorie"].map(lambda x: normalize_enum(x, cat_map, ""))
    if "importance" in df:
        df["importance"] = df["importance"].map(lambda x: normalize_enum(x, imp_map, ""))
    df = add_sequential_id(df, "RULE", "rule_id")
    return df, [], ["categorie", "importance"]


def process_mechanism_of_action(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], List[str]]:
    warnings: List[str] = []
    if "moa_id" in df and df["moa_id"].duplicated().any():
        warnings.append(f"Duplicate moa_id count: {int(df['moa_id'].duplicated().sum())}")
    if "risk_notes" in df:
        df["risk_notes"] = df["risk_notes"].map(lambda x: split_clean_join(x, separators=r"\||,"))
    return df, warnings, ["risk_notes", "moa_id"]


def process_clinical_guidelines(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], List[str]]:
    warnings: List[str] = []
    lot_map = {
        "1st_line": "1st Line",
        "first_line": "1st Line",
        "2nd_line": "2nd Line",
        "second_line": "2nd Line",
        "3rd_line": "3rd Line",
        "third_line": "3rd Line",
    }
    if "line_of_treatment" in df:
        df["line_of_treatment"] = df["line_of_treatment"].map(lambda x: normalize_enum(x, lot_map, ""))
        df["is_first_line"] = df["line_of_treatment"].eq("1st Line")
    if "guideline_id" in df:
        bad_fmt = (~df["guideline_id"].astype(str).str.match(r"^G\d+$", na=False)).sum()
        if bad_fmt:
            warnings.append(f"{int(bad_fmt)} guideline_id values do not match pattern G###.")
        if df["guideline_id"].duplicated().any():
            warnings.append(f"Duplicate guideline_id count: {int(df['guideline_id'].duplicated().sum())}")
    return df, warnings, ["line_of_treatment", "guideline_id"]


def run_validations(name: str, df: pd.DataFrame, refs: Dict[str, pd.DataFrame]) -> List[str]:
    warnings: List[str] = []
    if name == "doctors_clean.csv":
        if "id" in df and df["id"].duplicated().any():
            warnings.append("Duplicate id values found.")
        if {"latitude", "longitude"}.issubset(df.columns):
            out_bounds = df[(df["latitude"] < 30) | (df["latitude"] > 38) | (df["longitude"] < 7) | (df["longitude"] > 12)]
            if len(out_bounds):
                warnings.append(f"{len(out_bounds)} rows outside Tunisia coordinate bounds.")
    elif name == "pharmacies_clean.csv":
        if "id" in df and df["id"].duplicated().any():
            warnings.append("Duplicate id values found.")
        if "gouvernorat" in df:
            bad = (~df["gouvernorat"].isin(VALID_GOVERNORATES)).sum()
            if bad:
                warnings.append(f"{int(bad)} rows have invalid gouvernorat.")
        if "url_valid" not in df.columns:
            warnings.append("Missing required column: url_valid.")
    elif name == "vital_products_clean.csv":
        if "url" in df and df["url"].duplicated().any():
            warnings.append("Duplicate url values found.")
        if "name" in df and (df["name"].astype(str).str.strip() == "").any():
            warnings.append("Some rows have empty name.")
    elif name == "vital_product_knowledge_clean.csv":
        products = refs.get("vital_products_clean.csv")
        if products is not None and "name" in products and "nom_produit" in df:
            missing = set(df["nom_produit"].dropna().astype(str)) - set(products["name"].dropna().astype(str))
            if missing:
                warnings.append(f"{len(missing)} product names not matched in vital_products_clean.csv.")
    elif name in {
        "cosmetic_interactions_clean.csv",
        "drug_interactions_clean.csv",
        "ingredient_interactions_clean.csv",
    }:
        if "interaction_id" in df and df["interaction_id"].duplicated().any():
            warnings.append("Duplicate interaction_id values found.")
        if name == "ingredient_interactions_clean.csv" and "pair_key" in df and df["pair_key"].duplicated().any():
            warnings.append("Duplicate pair_key values found.")
    return warnings


def standardize_expected_columns(df: pd.DataFrame, expected: List[str]) -> pd.DataFrame:
    # Map existing normalized columns to normalized expected names where possible.
    existing_map = {normalize_key(c): c for c in df.columns}
    out = df.copy()
    for exp in expected:
        if exp not in out.columns:
            k = normalize_key(exp)
            if k in existing_map:
                out = out.rename(columns={existing_map[k]: exp})
            elif k.replace("_d_", "_") in existing_map:
                out = out.rename(columns={existing_map[k.replace("_d_", "_")]: exp})
            else:
                out[exp] = ""
    return out


def print_file_report(report: Dict[str, object]) -> None:
    print(f"\n--- Report: {report['output_file']} ---")
    print(f"Rows original: {report['rows_before']}")
    print(f"Rows cleaned:  {report['rows_after']}")
    print(f"Rows removed:  {report['rows_removed']}")
    print(f"Encoding fixes applied (estimate): {report['encoding_fixes']}")
    print(f"Columns with most issues: {', '.join(report['issue_columns']) if report['issue_columns'] else 'None'}")
    if report["warnings"]:
        print("Data quality warnings:")
        for w in report["warnings"]:
            print(f"  - {w}")
    else:
        print("Data quality warnings: none")


def main() -> None:
    os.makedirs(CLEAN_DIR, exist_ok=True)
    file_specs = [
        ("medecins.csv", "doctors_clean.csv", process_doctors, ["id", "nom", "prenom", "specialite", "telephone", "email", "adresse", "latitude", "longitude"]),
        ("pharmacies.csv", "pharmacies_clean.csv", process_pharmacies, ["id", "nom", "type", "telephone", "adresse", "gouvernorat", "url"]),
        ("vital_products_fixed.csv", "vital_products_clean.csv", process_vital_products, ["url", "name", "categories", "image", "indications", "forme", "infos_sur_le_produit", "classe", "compositions", "conseils_d_utilisation", "contre_indications"]),
        ("vital_ingredient_knowledge.csv", "vital_ingredients_clean.csv", process_vital_ingredients, ["ingredient", "categorie", "noms_alternatifs", "role", "synergies", "conflits", "precautions", "grossesse", "enfant", "senior", "diabetique", "dose_max_jour"]),
        ("vital_product_knowledge.csv", "vital_product_knowledge_clean.csv", process_vital_product_knowledge, ["nom_produit", "url", "categories", "classe", "forme", "indications", "compositions_brut", "ingredients_identifies", "ingredients_inconnus", "conseils_d_utilisation", "contre_indications_produit", "interactions_medicamenteuses", "alertes_grossesse", "alertes_enfant", "alertes_senior", "alertes_diabetique"]),
        ("general_cosmetic_interactions.csv", "cosmetic_interactions_clean.csv", process_cosmetic_interactions, ["actif_1", "actif_2", "type_interaction", "explication_detaillee", "conduite_a_tenir"]),
        ("general_drug_interactions.csv", "drug_interactions_clean.csv", process_drug_interactions, ["medicament", "supplement_substance", "type_interaction", "severite", "explication_detaillee", "conduite_a_tenir"]),
        ("general_ingredient_interactions.csv", "ingredient_interactions_clean.csv", process_ingredient_interactions, ["substance_1", "substance_2", "type_interaction", "explication_detaillee", "conduite_a_tenir"]),
        ("general_population_warnings.csv", "population_warnings_clean.csv", process_population_warnings, ["population_condition", "substance", "type_alerte", "severite", "explication_detaillee", "conduite_a_tenir"]),
        ("general_supplement_rules.csv", "supplement_rules_clean.csv", process_supplement_rules, ["categorie", "substance_sujet", "regle", "importance", "explication_detaillee", "conduite_a_tenir"]),
        ("mechanisms_of_action.csv", "mechanism_of_action_clean.csv", process_mechanism_of_action, ["moa_id", "mechanism_name", "biological_target", "physiological_effect", "therapeutic_benefit", "risk_notes"]),
        ("clinical_guideline_logic.csv", "clinical_guidelines_clean.csv", process_clinical_guidelines, ["guideline_id", "disease_name", "recommended_drug_class", "line_of_treatment", "decision_factors", "contraindications_summary"]),
    ]

    reports: List[Dict[str, object]] = []
    refs: Dict[str, pd.DataFrame] = {}

    for raw_name, out_name, processor, expected_cols in file_specs:
        print(f"\nProcessing file: {raw_name}")
        try:
            in_path = os.path.join(RAW_DIR, raw_name)
            if not os.path.exists(in_path):
                raise FileNotFoundError(f"Input file not found: {in_path}")
            df, used_encoding = try_read_csv(in_path)
            rows_before = len(df)
            df, common_stats = preprocess_common(df)
            df = standardize_expected_columns(df, expected_cols)
            df, proc_warnings, issue_cols = processor(df)
            df = df.fillna("")

            val_warnings = run_validations(out_name, df, refs)
            warnings = proc_warnings + val_warnings

            out_path = os.path.join(CLEAN_DIR, out_name)
            df.to_csv(out_path, index=False, encoding="utf-8-sig")

            report = {
                "raw_file": raw_name,
                "output_file": out_name,
                "encoding_used": used_encoding,
                "rows_before": rows_before,
                "rows_after": len(df),
                "rows_removed": rows_before - len(df),
                "encoding_fixes": common_stats["encoding_fixes"],
                "issue_columns": issue_cols,
                "warnings": warnings,
            }
            reports.append(report)
            refs[out_name] = df.copy()
            print_file_report(report)
        except Exception as exc:
            error_report = {
                "raw_file": raw_name,
                "output_file": out_name,
                "encoding_used": "",
                "rows_before": 0,
                "rows_after": 0,
                "rows_removed": 0,
                "encoding_fixes": 0,
                "issue_columns": [],
                "warnings": [f"Processing failed: {exc}"],
            }
            reports.append(error_report)
            print_file_report(error_report)

    if "vital_product_knowledge_clean.csv" in refs and "vital_products_clean.csv" in refs:
        knowledge = refs["vital_product_knowledge_clean.csv"]
        products = refs["vital_products_clean.csv"]
        if "nom_produit" in knowledge and "name" in products:
            missing = sorted(set(knowledge["nom_produit"]) - set(products["name"]))
            if missing:
                print(f"\nCross-check warning: {len(missing)} products in vital_product_knowledge_clean.csv not found in vital_products_clean.csv")

    print("\n=== Final Summary Table ===")
    summary = pd.DataFrame(
        [
            {
                "file": r["output_file"],
                "rows_before": r["rows_before"],
                "rows_after": r["rows_after"],
                "rows_removed": r["rows_removed"],
            }
            for r in reports
        ]
    )
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
