"""Download the 2025 Stack Overflow Developer Survey and write a slim CSV.

Run:  uv run python -m training.prepare_data
The raw file (141 MB) is cached under data/raw/ and gitignored. The slim CSV is committed.
"""

from pathlib import Path

import httpx
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
RAW_PATH = DATA_DIR / "raw" / "results.csv"
SLIM_PATH = DATA_DIR / "so_survey_2025_slim.csv"

RAW_URL = (
    "https://media.githubusercontent.com/media/StackExchange/Survey/main/"
    "packages/archive/2025/results.csv"
)

RAW_COLUMNS = [
    "Country",
    "WorkExp",
    "EdLevel",
    "DevType",
    "RemoteWork",
    "Age",
    "OrgSize",
    "LanguageHaveWorkedWith",
    "ConvertedCompYearly",
]

MIN_SALARY = 5_000
MAX_SALARY = 500_000
MAX_YEARS = 50


def download(url: str = RAW_URL, dest: Path = RAW_PATH) -> Path:
    if dest.exists():
        print(f"raw data already present at {dest}")
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"downloading {url} ...")
    with httpx.stream("GET", url, follow_redirects=True, timeout=600) as r:
        r.raise_for_status()
        with open(dest, "wb") as fh:
            for chunk in r.iter_bytes():
                fh.write(chunk)
    print(f"saved {dest.stat().st_size / 1e6:.0f} MB")
    return dest


def slim(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only rows with a usable salary and every feature present."""
    out = df[RAW_COLUMNS].copy()
    out = out[out["ConvertedCompYearly"].between(MIN_SALARY, MAX_SALARY)]
    out = out.dropna(subset=RAW_COLUMNS)
    out = out[out["Age"] != "Prefer not to say"]
    out = out[out["OrgSize"] != "I don’t know"]
    out["WorkExp"] = out["WorkExp"].clip(0, MAX_YEARS)
    return out.reset_index(drop=True)


def main() -> None:
    raw = download()
    df = pd.read_csv(raw, usecols=RAW_COLUMNS, low_memory=False)
    out = slim(df)
    out.to_csv(SLIM_PATH, index=False)
    print(f"wrote {len(out):,} rows to {SLIM_PATH}")


if __name__ == "__main__":
    main()
