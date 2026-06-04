import pandas as pd
import sys

def main():
    csv_path = "data/processed/phase3_clustered_claims.csv"
    df = pd.read_csv(csv_path)
    
    clusters = sorted([c for c in df["cluster_id"].unique() if c != -1])
    
    with open("scratch/clusters_detailed.txt", "w", encoding="utf-8") as out:
        for c in clusters:
            cluster_df = df[df["cluster_id"] == c]
            size = len(cluster_df)
            org_breakdown = cluster_df["organism"].value_counts().to_dict()
            org_str = ", ".join([f"{org}: {count} ({count/size*100:.1f}%)" for org, count in org_breakdown.items()])
            
            out.write("=" * 80 + "\n")
            out.write(f"CLUSTER {c} | Size: {size} | Organism Distribution: {org_str}\n")
            out.write("=" * 80 + "\n")
            
            core_claims = cluster_df.sort_values(by="cluster_probability", ascending=False).head(30)
            for idx, row in enumerate(core_claims.itertuples(), 1):
                out.write(f"{idx}. [{row.organism}] {row.claim} (Prob: {row.cluster_probability:.3f})\n")
            out.write("\n\n")

if __name__ == "__main__":
    main()
