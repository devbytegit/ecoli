"""
verify_data.py
==============
Checks every hardcoded number used in the figures against the actual CSV files.
Run this before/after figure generation to confirm 100% accuracy.
"""
import os
import pandas as pd
import numpy as np

BASE  = r"C:\Users\olufi\Desktop\QUICK FILES\ECOLI"
DATA  = os.path.join(BASE, "data")
PROC  = os.path.join(DATA, "processed")
RAW   = os.path.join(DATA, "raw")

print("=" * 65)
print("DATA VERIFICATION REPORT")
print("=" * 65)

df_raw    = pd.read_csv(os.path.join(RAW,  "corpus_raw.csv"))
df_claims = pd.read_csv(os.path.join(PROC, "phase3_clustered_claims.csv"))
df_sum    = pd.read_csv(os.path.join(PROC, "phase3_cluster_summary.csv"))

# ── SECTION 1: Corpus counts ────────────────────────────────────────────────
print("\n[1] CORPUS PAPER COUNTS (used in Fig 1 x-axis labels)")
org_counts = df_raw["organism"].value_counts()
print(org_counts.to_string())
ecoli_n  = org_counts.get("E. coli", 0)
yeast_n  = org_counts.get("S. cerevisiae", 0)
bacil_n  = org_counts.get("B. subtilis", 0)
total_n  = len(df_raw)
print(f"\n  Total papers in corpus_raw.csv: {total_n}")
print(f"  Fig labels used: E. coli n=2,051  | actual: {ecoli_n}")
print(f"  Fig labels used: S. cerevisiae n=950 | actual: {yeast_n}")
print(f"  Fig labels used: B. subtilis n=272   | actual: {bacil_n}")

# ── SECTION 2: Justification rates ──────────────────────────────────────────
print("\n[2] JUSTIFICATION RATES (used in Fig 1 bar heights & Fig 2 donut)")
print("    (justification_type or similar column needed)")
print()
print("  Columns in corpus_raw.csv:", list(df_raw.columns))

if "justification_type" in df_raw.columns:
    jt_col = "justification_type"
elif "has_justification" in df_raw.columns:
    jt_col = "has_justification"
elif "justification" in df_raw.columns:
    jt_col = "justification"
else:
    jt_col = None
    print("  WARNING: No justification column found in corpus_raw.csv")

if jt_col:
    for org in ["E. coli", "S. cerevisiae", "B. subtilis"]:
        sub = df_raw[df_raw["organism"] == org]
        n   = len(sub)
        if n == 0:
            continue
        null_mask = sub[jt_col].isna() | (sub[jt_col].astype(str).str.lower().isin(
            ["null", "none", "no", "nan", "0", "false", ""]))
        null_n = null_mask.sum()
        expl_n = n - null_n
        null_pct = round(null_n / n * 100, 1)
        expl_pct = round(expl_n / n * 100, 1)
        print(f"  {org:<20}  n={n:>5}  null={null_pct:>5}%  explicit={expl_pct:>5}%")
    print()
    print("  Fig 1 hardcoded: E.coli null=61.5%, explicit=38.5%")
    print("  Fig 1 hardcoded: S.cer  null=31.1%, explicit=68.9%")
    print("  Fig 1 hardcoded: B.sub  null=32.0%, explicit=68.0%")

# Also check via claims data (alternative source)
print("\n  --- Claims-based check (phase3_clustered_claims.csv) ---")
print("  Columns:", list(df_claims.columns))

# ── SECTION 3: Cluster counts ────────────────────────────────────────────────
print("\n[3] CLUSTER COUNTS (used in Fig 4 Treemap)")
ecoli_cl = df_claims[(df_claims["organism"] == "E. coli") &
                     (df_claims["cluster_id"] >= 0)]
print(f"  E. coli clustered claims total: {len(ecoli_cl)}")
print(f"  Fig 4 title says: 458")
by_cluster = ecoli_cl.groupby("cluster_id").size().sort_values(ascending=False)
print("\n  Per-cluster E. coli claim counts:")
print(by_cluster.to_string())

# ── SECTION 4: Total clustered claims ────────────────────────────────────────
print("\n[4] TOTAL CLAIMS (used in Fig 5 UMAP title)")
all_clustered = df_claims[df_claims["cluster_id"] != -1]
print(f"  Total non-noise claims: {len(all_clustered)}")
print(f"  Fig 5 title says: 2,037")
print(f"  Total rows in claims file: {len(df_claims)}")

# ── SECTION 5: Decade distribution ───────────────────────────────────────────
print("\n[5] DECADE DISTRIBUTION (used in Fig 3)")
df_raw["decade"] = (df_raw["year"].astype(int) // 10) * 10
dec_org = df_raw.groupby(["decade", "organism"]).size().unstack(fill_value=0)
print(dec_org.to_string())

# ── SECTION 6: Organism x Cluster matrix ────────────────────────────────────
print("\n[6] ORGANISM x CLUSTER MATRIX (used in Fig 9 heatmap & Fig 8 radar)")
org_cl = (df_claims[df_claims["cluster_id"] >= 0]
          .groupby(["organism", "cluster_id"]).size().unstack(fill_value=0))
org_norm = org_cl.div(org_cl.sum(axis=1), axis=0) * 100
print(org_norm.round(1).to_string())

print("\n" + "=" * 65)
print("VERIFICATION COMPLETE")
print("=" * 65)
