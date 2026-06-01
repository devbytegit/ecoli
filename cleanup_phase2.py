import pandas as pd
from pathlib import Path

csv_path = Path("data/processed/phase2_claims.csv")
clean_csv_path = Path("data/processed/phase2_claims_clean.csv")
phase3_input_path = Path("data/processed/phase3_input.csv")

if not csv_path.exists():
    print(f"Error: {csv_path} does not exist!")
    exit(1)

# Load CSV
df = pd.read_csv(csv_path)
print(f"Original claims file loaded: {len(df)} rows")

# Step 1: Remove hallucinated claims
# Filter out rows where hallucination_risk is True (keep False or NaN/None)
clean = df[df["hallucination_risk"] != True]
clean.to_csv(clean_csv_path, index=False)
removed_hallucinations = len(df) - len(clean)
print(f"Removed: {removed_hallucinations} hallucinated claims")
print(f"Clean claims ready (saved to phase2_claims_clean.csv): {len(clean)}")

# Step 2: Filter to explicit reasons only
claims_only = clean[clean["explicit_reason_found"] == True]
claims_only.to_csv(phase3_input_path, index=False)
print(f"Claims ready for clustering (saved to phase3_input.csv): {len(claims_only)}")
