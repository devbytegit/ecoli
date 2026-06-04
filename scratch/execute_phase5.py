import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    print("="*60)
    print("PHASE 5: TEMPORAL ANALYSIS OF E. COLI THEMATIC JUSTIFICATIONS")
    print("="*60)
    
    csv_path = "data/processed/phase3_clustered_claims.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found!")
        return

    df = pd.read_csv(csv_path)
    
    # Filter to E. coli and exclude noise
    df_eco = df[(df["organism"] == "E. coli") & (df["cluster_id"] != -1)].copy()
    print(f"Total clustered E. coli claims for temporal analysis: {len(df_eco)}")
    
    # Define short theme names for E. coli clusters for cleaner plotting
    theme_names = {
        4: "Experimental Rationale",
        5: "Standard Bacterium Utility",
        6: "Heterologous Expression Host",
        7: "Clinical Pathogenesis Modeling",
        8: "Gram-Negative Reference",
        9: "Antimicrobial Screening",
        10: "DNA Replication & Repair",
        11: "Bacterial Reference Standard",
        12: "Genomic Annotation Reference"
    }
    
    df_eco["theme"] = df_eco["cluster_id"].map(theme_names)
    
    # Bin by decade
    bins = [1989, 1999, 2009, 2019, 2026]
    labels = ["1990-1999", "2000-2009", "2010-2019", "2020-2025"]
    df_eco["decade"] = pd.cut(df_eco["year"], bins=bins, labels=labels)
    
    # Check counts per decade
    decade_counts = df_eco["decade"].value_counts().sort_index()
    print("\nClaims per decade bin:")
    for dec, count in decade_counts.items():
        print(f"  {dec}: {count} claims")
        
    # Calculate cross-tabulation in percentages
    cross_tab = pd.crosstab(df_eco["decade"], df_eco["theme"], normalize="index") * 100
    
    # Save CSV of trends
    os.makedirs("data/processed", exist_ok=True)
    cross_tab.to_csv("data/processed/phase5_temporal_trends.csv")
    print(f"\nSaved temporal trend data to 'data/processed/phase5_temporal_trends.csv'")
    
    # Plotting
    os.makedirs("data/figures", exist_ok=True)
    fig_path = "data/figures/phase5_temporal.png"
    
    plt.figure(figsize=(18, 8), dpi=300)
    sns.set_theme(style="whitegrid")
    
    # Elegant color palette for 9 themes
    colors = sns.color_palette("Set3", 9)
    
    # Panel 1: Stacked Bar Chart
    plt.subplot(1, 2, 1)
    cross_tab.plot(kind="bar", stacked=True, color=colors, ax=plt.gca(), width=0.6)
    plt.title("Thematic Shifts in E. coli Justifications (Stacked Bar)", fontsize=14, weight="bold", pad=15)
    plt.xlabel("Decade Bin", fontsize=12)
    plt.ylabel("Relative Frequency (%)", fontsize=12)
    plt.xticks(rotation=0)
    plt.legend().remove() # We'll show a single legend in the middle/right
    
    # Panel 2: Line Plot
    plt.subplot(1, 2, 2)
    for i, col in enumerate(cross_tab.columns):
        plt.plot(cross_tab.index, cross_tab[col], marker="o", linewidth=2.5, color=colors[i], label=col)
    
    plt.title("Trajectory of Individual Research Themes (Line)", fontsize=14, weight="bold", pad=15)
    plt.xlabel("Decade Bin", fontsize=12)
    plt.ylabel("Frequency within E. coli Claims (%)", fontsize=12)
    plt.ylim(-2, 45)
    
    # Shared Legend
    plt.legend(title="Research Themes", bbox_to_anchor=(1.05, 1), loc="upper left", title_fontsize=12, fontsize=10)
    
    plt.tight_layout()
    plt.savefig(fig_path, bbox_inches="tight")
    plt.close()
    print(f"Saved temporal trend plot to '{fig_path}'")
    print("Phase 5 Temporal Analysis completed successfully!\n")

if __name__ == "__main__":
    main()
