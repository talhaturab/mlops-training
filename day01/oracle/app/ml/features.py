"""Feature definitions shared by training and serving.

If you change anything here you must retrain (make train) and redeploy, because the
model artifact was fitted against these exact columns and categories.
"""

import pandas as pd

# Roughly the 30 most common countries in the 2025 survey (among rows with a salary).
COUNTRIES = [
    "United States of America",
    "Germany",
    "United Kingdom of Great Britain and Northern Ireland",
    "France",
    "Canada",
    "India",
    "Netherlands",
    "Italy",
    "Brazil",
    "Australia",
    "Poland",
    "Spain",
    "Ukraine",
    "Sweden",
    "Switzerland",
    "Czech Republic",
    "Austria",
    "Denmark",
    "Portugal",
    "Belgium",
    "Romania",
    "Finland",
    "Norway",
    "New Zealand",
    "Greece",
    "Israel",
    "South Africa",
    "Mexico",
    "Hungary",
    "Ireland",
]
OTHER_COUNTRY = "Other"

_COUNTRY_ALIASES = {
    "usa": "United States of America",
    "us": "United States of America",
    "united states": "United States of America",
    "america": "United States of America",
    "uk": "United Kingdom of Great Britain and Northern Ireland",
    "united kingdom": "United Kingdom of Great Britain and Northern Ireland",
    "england": "United Kingdom of Great Britain and Northern Ireland",
    "great britain": "United Kingdom of Great Britain and Northern Ireland",
    "czechia": "Czech Republic",
    "holland": "Netherlands",
}

ED_LEVELS = [
    "Primary/elementary school",
    "Secondary school (e.g. American high school, German Realschule or Gymnasium, etc.)",
    "Some college/university study without earning a degree",
    "Associate degree (A.A., A.S., etc.)",
    "Bachelor’s degree (B.A., B.S., B.Eng., etc.)",
    "Master’s degree (M.A., M.S., M.Eng., MBA, etc.)",
    "Professional degree (JD, MD, Ph.D, Ed.D, etc.)",
    "Other (please specify):",
]

DEV_TYPES = [
    "Developer, full-stack",
    "Developer, back-end",
    "Developer, front-end",
    "Developer, mobile",
    "Developer, desktop or enterprise applications",
    "Developer, embedded applications or devices",
    "Architect, software or solutions",
    "Engineering manager",
    "DevOps engineer or professional",
    "Cloud infrastructure engineer",
    "Data engineer",
    "Data scientist",
    "AI/ML engineer",
    "Academic researcher",
    "Senior executive (C-suite, VP, etc.)",
    "Other (please specify):",
]

REMOTE_WORK = [
    "Remote",
    "Hybrid (some in-person, leans heavy to flexibility)",
    "Hybrid (some remote, leans heavy to in-person)",
    "Your choice (very flexible, you can come in when you want or just as needed)",
    "In-person",
]

AGE_BANDS = [
    "18-24 years old",
    "25-34 years old",
    "35-44 years old",
    "45-54 years old",
    "55-64 years old",
    "65 years or older",
]

ORG_SIZES = [
    "Just me - I am a freelancer, sole proprietor, etc.",
    "Less than 20 employees",
    "20 to 99 employees",
    "100 to 499 employees",
    "500 to 999 employees",
    "1,000 to 4,999 employees",
    "5,000 to 9,999 employees",
    "10,000 or more employees",
]

# Normalized language name -> column slug.
LANGUAGE_SLUGS = {
    "python": "python",
    "sql": "sql",
    "javascript": "javascript",
    "typescript": "typescript",
    "java": "java",
    "c#": "csharp",
    "c++": "cpp",
    "go": "go",
    "rust": "rust",
    "bash/shell": "bash",
}
LANGUAGES = list(LANGUAGE_SLUGS)

RELATIONSHIP_STATUSES = ["single", "dating", "engaged", "it's complicated"]

CATEGORICAL_COLUMNS = ["country", "ed_level", "dev_type", "remote_work", "age_band", "org_size"]
NUMERIC_COLUMNS = ["years_pro"]
LANGUAGE_COLUMNS = [f"lang_{slug}" for slug in LANGUAGE_SLUGS.values()]
FEATURE_COLUMNS = CATEGORICAL_COLUMNS + NUMERIC_COLUMNS + LANGUAGE_COLUMNS

MARRIAGE_FEATURES = [
    "age",
    "relationship_status",
    "coffee_cups_per_day",
    "coding_hours_per_week",
    "side_projects",
    "unread_slack_messages",
]

MAX_YEARS_PRO = 50


def normalize_language(name: str) -> str:
    """'Bash/Shell (all shells)' -> 'bash/shell'."""
    return name.split(" (")[0].strip().lower()


def normalize_country(name: str) -> str:
    """Map free text to one of COUNTRIES or OTHER_COUNTRY."""
    cleaned = name.strip()
    if cleaned in COUNTRIES:
        return cleaned
    lowered = cleaned.lower()
    if lowered in _COUNTRY_ALIASES:
        return _COUNTRY_ALIASES[lowered]
    for country in COUNTRIES:
        if country.lower() == lowered:
            return country
    return OTHER_COUNTRY


def build_feature_frame(records: list[dict]) -> pd.DataFrame:
    """Turn request-shaped dicts into the exact DataFrame the income model expects.

    Each record has keys: country, years_pro, ed_level, dev_type, remote_work,
    age_band, org_size, languages (list of str).
    """
    rows = []
    for r in records:
        langs = {normalize_language(lang) for lang in r.get("languages", [])}
        row = {
            "country": normalize_country(r["country"]),
            "years_pro": min(max(int(r["years_pro"]), 0), MAX_YEARS_PRO),
            "ed_level": r["ed_level"],
            "dev_type": r["dev_type"],
            "remote_work": r["remote_work"],
            "age_band": r["age_band"],
            "org_size": r["org_size"],
        }
        for lang, slug in LANGUAGE_SLUGS.items():
            row[f"lang_{slug}"] = int(lang in langs)
        rows.append(row)
    return pd.DataFrame(rows, columns=FEATURE_COLUMNS)
