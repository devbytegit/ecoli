"""Verify corpus integrity — exact paper count."""
import pandas as pd
from pathlib import Path

csv = Path("data/raw/corpus_raw.csv")
df = pd.read_csv(csv, dtype=str).fillna("")

print("=== CORPUS INTEGRITY CHECK ===")
print(f"Total rows          : {len(df)}")
print(f"Unique paper_ids    : {df['paper_id'].nunique()}")
print(f"Duplicates          : {len(df) - df['paper_id'].nunique()}")
print()
print("By organism:")
for org, count in df["organism"].value_counts().items():
    print(f"  {org:20s}: {count}")
print()
years = pd.to_numeric(df["year"], errors="coerce").dropna()
print(f"Year range          : {int(years.min())} - {int(years.max())}")
print()
empty = df[df["abstract"].str.strip().str.len() < 30]
print(f"Short abstracts     : {len(empty)}")
print()

claims = Path("data/processed/phase2_claims.jsonl")
failed = Path("data/processed/phase2_failed.jsonl")
print("=== OUTPUT FILES ===")
print(f"phase2_claims.jsonl : {'EXISTS' if claims.exists() else 'CLEAN SLATE'}")
print(f"phase2_failed.jsonl : {'EXISTS' if failed.exists() else 'CLEAN SLATE'}")
print()
print(f"==> Phase 2 will process: {len(df)} papers")
