import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

BASE = r"C:\Users\olufi\Desktop\QUICK FILES\ECOLI"
FIGS = os.path.join(BASE, "data", "figures")
PROC = os.path.join(BASE, "data", "processed")
C_ECOLI, C_YEAST, C_BACILLUS, C_BG = "#1B6CA8", "#9C4F96", "#2EAA6E", "#F7F9FC"

df_claims = pd.read_csv(os.path.join(PROC, "phase3_clustered_claims.csv"))

SHORT_NAMES_RADAR = {
     0: "Spore Physiology",  1: "Gram+ Definition",   2: "Eukaryotic Biology",
     3: "Genetic Tractability", 4: "Org. Selection",  5: "Standard Model Bacterium",
     6: "Recombinant Expr.", 7: "Pathogenesis",        8: "Gram-Neg Ref.",
     9: "Antimicrobials",   10: "DNA Replication",    11: "Bacterial Ref Std",
    12: "Genomic Annotation",
}

org_counts = (df_claims[df_claims["cluster_id"] >= 0]
              .groupby(["organism", "cluster_id"]).size().unstack(fill_value=0))
org_norm = org_counts.div(org_counts.sum(axis=1), axis=0) * 100

cats = [c for c in range(13) if c in org_norm.columns]
cat_labels = [SHORT_NAMES_RADAR.get(c, str(c)) for c in cats]
N = len(cats)
angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
angles += angles[:1]

def make_radar(bbox, loc, name):
    fig = plt.figure(figsize=(11, 9), facecolor=C_BG)
    ax = fig.add_axes([0.16, 0.10, 0.52, 0.52], projection="polar")
    ax.set_facecolor(C_BG)

    for org, color, alpha in [("E. coli", C_ECOLI, 0.25),
                               ("S. cerevisiae", C_YEAST, 0.25),
                               ("B. subtilis", C_BACILLUS, 0.25)]:
        if org not in org_norm.index:
            continue
        vals = [org_norm.loc[org, c] if c in org_norm.columns else 0 for c in cats]
        vals += vals[:1]
        ax.plot(angles, vals, color=color, linewidth=2.5, linestyle="solid", label=org)
        ax.fill(angles, vals, color=color, alpha=alpha)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([])
    ax.set_rlabel_position(30)
    ax.set_yticks([10, 20, 30, 40, 50, 60])
    ax.set_yticklabels(["10%", "20%", "30%", "40%", "50%", "60%"],
                       fontsize=8, color="#888888")
    ax.set_ylim(0, 65)
    ax.grid(color="#CCCCCC", linestyle="--", linewidth=0.8)
    ax.spines["polar"].set_color("#CCCCCC")

    LABEL_R = 76
    for i, (angle, label) in enumerate(zip(angles[:-1], cat_labels)):
        angle_deg = np.degrees(angle)
        
        if abs(angle_deg - 90) < 5:
            ha = "center"
            va = "bottom"
        elif abs(angle_deg - 270) < 5:
            ha = "center"
            va = "top"
        elif angle_deg < 90 or angle_deg > 270:
            ha = "left"
            va = "center"
        else:
            ha = "right"
            va = "center"

        ax.text(
            angle, LABEL_R,
            label,
            ha=ha,
            va=va,
            fontsize=8.5,
            fontweight="bold",
            color="#333333",
            rotation=0,
        )

    ax.legend(loc=loc, bbox_to_anchor=bbox, fontsize=10, framealpha=0.9)
    fig.suptitle(
        "Organism Research Profile Radar Chart\n"
        f"Normalized Justification Distribution (Legend: {name})",
        fontsize=13, fontweight="bold", y=0.88
    )

    output_file = os.path.join(FIGS, f"test_fig8_{name}.png")
    plt.savefig(output_file, dpi=200, bbox_inches="tight")
    plt.close()
    print("Saved test fig8 to:", output_file)

# Test 1: Legend upper-right corner of the canvas (loc="upper left", bbox_to_anchor=(1.2, 0.95))
make_radar((1.2, 0.95), "upper left", "top_right")

# Test 2: Legend bottom-right corner of the canvas (loc="lower left", bbox_to_anchor=(1.2, 0.05))
make_radar((1.2, 0.05), "lower left", "bottom_right")

# Test 3: Legend centered vertically but pushed further right (loc="center left", bbox_to_anchor=(1.35, 0.5))
make_radar((1.35, 0.5), "center left", "pushed_right")
