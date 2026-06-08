import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    print("="*60)
    print("PHASE 6: CROSS-ORGANISM COMPARATIVE ANALYSIS")
    print("="*60)
    
    csv_path = "data/processed/phase3_clustered_claims.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found!")
        return

    df = pd.read_csv(csv_path)
    
    # Filter out noise
    df_clean = df[df["cluster_id"] != -1].copy()
    print(f"Total clustered claims (excluding noise): {len(df_clean)}")
    
    theme_names = {
        0: "0. Gram-Pos Physiology & Bioprocess (Bs)",
        1: "1. Gram-Pos Bacterium Definition (Bs)",
        2: "2. Eukaryotic Biology & Disease Model (Sc)",
        3: "3. Genetic Tractability & Workhorse Tools (Sc/Bs)",
        4: "4. Experimental Selection Rationale (Ec)",
        5: "5. Standard Bacterium Utility (Ec)",
        6: "6. Heterologous Expression Host (Ec)",
        7: "7. Clinical Pathogenesis Modeling (Ec)",
        8: "8. Gram-Negative Reference (Ec)",
        9: "9. Antimicrobial Screening (Ec)",
        10: "10. DNA Replication & Repair (Ec)",
        11: "11. Bacterial Reference Standard (Ec)",
        12: "12. Genomic Annotation Reference (Ec)"
    }
    
    df_clean["theme"] = df_clean["cluster_id"].map(theme_names)
    
    # Calculate crosstab: Theme x Organism, normalized by column (organism total)
    cross_tab = pd.crosstab(df_clean["theme"], df_clean["organism"], normalize="columns") * 100
    
    # Reorder columns for logical presentation: E. coli, S. cerevisiae, B. subtilis
    columns_order = ["E. coli", "S. cerevisiae", "B. subtilis"]
    cross_tab = cross_tab[columns_order]
    
    # Save comparison CSV
    os.makedirs("data/processed", exist_ok=True)
    cross_tab.to_csv("data/processed/phase6_comparison.csv")
    print(f"Saved comparative matrix to 'data/processed/phase6_comparison.csv'")
    
    # Plotting Heatmap
    os.makedirs("data/figures", exist_ok=True)
    fig_path = "data/figures/phase6_comparison_heatmap.png"
    
    plt.figure(figsize=(10, 8), dpi=300)
    sns.set_theme(style="white")
    
    # Heatmap with YlGnBu colormap
    sns.heatmap(
        cross_tab,
        annot=True,
        fmt=".1f",
        cmap="YlGnBu",
        linewidths=0.5,
        cbar_kws={'label': 'Percentage of Organism Claims (%)'},
        annot_kws={"size": 11, "weight": "bold"}
    )
    
    plt.title("Functional Profile Heatmap: E. coli vs. Yeast and Bacillus", fontsize=14, weight="bold", pad=20)
    plt.xlabel("Model Microorganisms", fontsize=12, labelpad=10)
    plt.ylabel("Scientific Justification Themes", fontsize=12, labelpad=10)
    plt.xticks(fontsize=11)
    plt.yticks(fontsize=10, rotation=0)
    
    plt.tight_layout()
    plt.savefig(fig_path, bbox_inches="tight")
    plt.close()
    print(f"Saved comparative heatmap to '{fig_path}'")
    print("Phase 6 Comparative Analysis completed successfully!\n")

if __name__ == "__main__":
    main()
