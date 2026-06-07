"""
generate_figures.py  (fixed v2)
================================
Generates all 9 publication-quality figures.
All special Unicode characters removed from matplotlib text strings
to avoid cp1252 rendering corruption on Windows.
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.patches import FancyBboxPatch
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
import seaborn as sns
import networkx as nx

# Force UTF-8 stdout so print() works even on cp1252 terminals
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

warnings.filterwarnings("ignore")

# --- PATHS ------------------------------------------------------------------
BASE  = r"C:\Users\olufi\Desktop\QUICK FILES\ECOLI"
DATA  = os.path.join(BASE, "data")
FIGS  = os.path.join(DATA, "figures")
PROC  = os.path.join(DATA, "processed")
RAW   = os.path.join(DATA, "raw")
os.makedirs(FIGS, exist_ok=True)

# --- GLOBAL STYLE -----------------------------------------------------------
plt.rcParams.update({
    "font.family":      "DejaVu Sans",
    "font.size":        11,
    "axes.titlesize":   14,
    "axes.labelsize":   12,
    "axes.spines.top":  False,
    "axes.spines.right":False,
    "figure.dpi":       150,
    "savefig.dpi":      300,
    "savefig.bbox":     "tight",
    "savefig.facecolor":"white",
})

# --- PALETTE ----------------------------------------------------------------
C_ECOLI     = "#1B6CA8"
C_YEAST     = "#9C4F96"
C_BACILLUS  = "#2EAA6E"
C_NULL      = "#D64045"
C_EXPLICIT  = "#4CAF7D"
C_ACCENT    = "#F4A261"
C_BG        = "#F7F9FC"

ORG_COLORS = {
    "E. coli":       C_ECOLI,
    "S. cerevisiae": C_YEAST,
    "B. subtilis":   C_BACILLUS,
}

# --- LOAD DATA --------------------------------------------------------------
print("Loading data...")
df_claims  = pd.read_csv(os.path.join(PROC, "phase3_clustered_claims.csv"))
df_summary = pd.read_csv(os.path.join(PROC, "phase3_cluster_summary.csv"))
df_raw     = pd.read_csv(os.path.join(RAW,  "corpus_raw.csv"))
df_temp    = pd.read_csv(os.path.join(PROC, "phase5_temporal_trends.csv"))
df_comp    = pd.read_csv(os.path.join(PROC, "phase6_comparison.csv"))
df_pathway = pd.read_csv(os.path.join(PROC, "phase4_pathway_map.csv"))
print("Data loaded.\n")

# --- SHORT THEME NAMES (ASCII only, no em-dashes) ---------------------------
SHORT_NAMES = {
    -1: "Noise",
     0: "B.sub Spore\n& Physiology",
     1: "B.sub Model\nDefinition",
     2: "Yeast Eukaryotic\nBiology",
     3: "Genetic\nTractability",
     4: "Organism\nSelection",
     5: "Standard Model\nBacterium",
     6: "Recombinant\nExpression",
     7: "Clinical\nPathogenesis",
     8: "Gram-Neg\nReference",
     9: "Antimicrobial\nScreening",
    10: "DNA Replication\n& Repair",
    11: "Bacterial Ref\nStandard",
    12: "Genomic\nAnnotation",
}

SHORT_NAMES_RADAR = {
     0: "Spore Physiology",
     1: "Gram+ Definition",
     2: "Eukaryotic Biology",
     3: "Genetic Tractability",
     4: "Org. Selection",
     5: "Standard Bacterium",
     6: "Recombinant Expr.",
     7: "Pathogenesis",
     8: "Gram-Neg Ref.",
     9: "Antimicrobials",
    10: "DNA Replication",
    11: "Bacterial Ref Std",
    12: "Genomic Annotation",
}

# ============================================================================
# FIGURE 1 -- Grouped Bar: Axiomatic Acceptance Gap
# ============================================================================
print("Figure 1 - Axiomatic Acceptance Gap...")

organisms = ["E. coli", "S. cerevisiae", "B. subtilis"]
null_pct  = [61.6, 31.2, 32.4]   # exact from data
expl_pct  = [38.4, 68.8, 67.6]   # exact from data
x = np.arange(len(organisms))
w = 0.36

fig, ax = plt.subplots(figsize=(9, 6), facecolor=C_BG)
ax.set_facecolor(C_BG)

bars_null = ax.bar(x - w/2, null_pct, w, color=C_NULL,    label="No Justification (Null)",
                   zorder=3, edgecolor="white", linewidth=0.8)
bars_expl = ax.bar(x + w/2, expl_pct, w, color=C_EXPLICIT, label="Explicit Justification",
                   zorder=3, edgecolor="white", linewidth=0.8)

# value labels above each bar
for bar, val in zip(bars_null, null_pct):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.2,
            f"{val}%", ha="center", va="bottom", fontsize=11, fontweight="bold",
            color=C_NULL)
for bar, val in zip(bars_expl, expl_pct):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.2,
            f"{val}%", ha="center", va="bottom", fontsize=11, fontweight="bold",
            color="#2D7A50")

ax.axhline(50, color="#AAAAAA", linestyle="--", linewidth=1.2, zorder=2, label="50% baseline")
ax.set_xticks(x)
ax.set_xticklabels(
    ["E. coli\n(n=2,051)", "S. cerevisiae\n(n=950)", "B. subtilis\n(n=272)"],  # verified counts
    fontsize=11, fontweight="bold")
ax.set_ylabel("Percentage of Papers (%)", fontsize=12)
ax.set_ylim(0, 90)
ax.set_yticks(range(0, 91, 10))
ax.yaxis.set_tick_params(labelsize=10)

# Legend: put at top-right, away from annotation
ax.legend(fontsize=10, loc="upper right", framealpha=0.9)
ax.set_title(
    "The Axiomatic Acceptance Gap\nJustification Rates Across Model Microorganisms",
    fontsize=14, fontweight="bold", pad=14)
ax.grid(axis="y", linestyle="--", alpha=0.5, zorder=1)

# Annotation arrow: stays LEFT of E. coli bars (negative x offset)
# Point to the top of E. coli's# annotation: 30.4 pp gap label — stays far left of the E. coli bars
ax.annotate(
    "30.4 pp gap\n(Axiomatic\nAcceptance)",
    xy=(x[0] + w/2, expl_pct[0] + 1),      # arrowhead: top of E. coli green bar
    xytext=(x[0] - 0.60, 75),               # label: left side above E. coli
    fontsize=9, color="#333333",
    ha="center",
    arrowprops=dict(arrowstyle="->", color="#555555", lw=1.3,
                    connectionstyle="arc3,rad=0.30"))

plt.tight_layout()
plt.savefig(os.path.join(FIGS, "fig1_axiomatic_acceptance_gap.png"))
plt.close()
print("  -> Saved fig1_axiomatic_acceptance_gap.png")

# ============================================================================
# FIGURE 2 -- Donut: E. coli Null vs Explicit
# ============================================================================
print("Figure 2 - E. coli Donut...")

# wider figure so labels on both sides have room
fig, ax = plt.subplots(figsize=(9, 7), facecolor=C_BG)
ax.set_facecolor(C_BG)

# exact values from data
sizes   = [61.6, 38.4]
colors  = [C_NULL, C_EXPLICIT]
explode = (0.05, 0)

wedges, _ = ax.pie(
    sizes, labels=None, colors=colors, explode=explode,
    startangle=90,
    wedgeprops=dict(width=0.52, edgecolor="white", linewidth=3))

# centre text inside the donut hole
ax.text(0,  0.10, "E. coli",   ha="center", va="center",
        fontsize=16, fontweight="bold", color="#222222")
ax.text(0, -0.14, "n = 2,051", ha="center", va="center",
        fontsize=11, color="#555555")

# Annotate with arrows so labels sit safely OUTSIDE and don't clip
ax.annotate(
    "No Justification\n(Null)\n61.6%",
    xy=(-0.55, 0.60), xytext=(-1.55, 0.80),
    fontsize=11, fontweight="bold", color=C_NULL, ha="center",
    arrowprops=dict(arrowstyle="->", color=C_NULL, lw=1.2))

ax.annotate(
    "Explicit\nJustification\n38.4%",
    xy=(0.50, -0.55), xytext=(1.50, -0.80),
    fontsize=11, fontweight="bold", color="#2D7A50", ha="center",
    arrowprops=dict(arrowstyle="->", color="#2D7A50", lw=1.2))

ax.set_xlim(-2.1, 2.1)   # extra horizontal space for annotations
ax.set_ylim(-1.5, 1.5)

ax.set_title(
    "E. coli - Justification Split\nAcross 2,051 Peer-Reviewed Papers",
    fontsize=14, fontweight="bold", pad=16)

plt.tight_layout()
plt.savefig(os.path.join(FIGS, "fig2_ecoli_donut.png"))
plt.close()
print("  -> Saved fig2_ecoli_donut.png")

# ============================================================================
# FIGURE 3 -- Grouped Bar: Corpus Composition by Organism + Decade
# ============================================================================
print("Figure 3 - Corpus composition...")

df_raw["decade"] = (df_raw["year"].astype(int) // 10) * 10
# Use plain ASCII hyphens -- no em-dashes
decade_map = {1990: "1990-1999", 2000: "2000-2009",
              2010: "2010-2019", 2020: "2020-2025"}
df_raw["decade_label"] = df_raw["decade"].map(decade_map)

decade_order = ["1990-1999", "2000-2009", "2010-2019", "2020-2025"]
counts = df_raw.groupby(["decade_label", "organism"]).size().unstack(fill_value=0)
counts = counts.reindex(decade_order)
for o in ["E. coli", "S. cerevisiae", "B. subtilis"]:
    if o not in counts.columns:
        counts[o] = 0
counts = counts[["E. coli", "S. cerevisiae", "B. subtilis"]]

x = np.arange(len(decade_order))
w = 0.25

fig, ax = plt.subplots(figsize=(10, 6), facecolor=C_BG)
ax.set_facecolor(C_BG)

for i, (org, color) in enumerate(ORG_COLORS.items()):
    vals = counts[org].values
    bars = ax.bar(x + (i-1)*w, vals, w, color=color, label=org,
                  zorder=3, edgecolor="white", linewidth=0.8)
    for bar, v in zip(bars, vals):
        if v > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3,
                    str(v), ha="center", va="bottom", fontsize=9, fontweight="bold",
                    color=color)

ax.set_xticks(x)
ax.set_xticklabels(decade_order, fontsize=11)
ax.set_ylabel("Number of Papers", fontsize=12)
ax.set_title(
    "Corpus Composition by Organism and Decade\n"
    "(3,273 Unique Peer-Reviewed Papers, 1990-2025)",
    fontsize=14, fontweight="bold")
ax.legend(fontsize=11, loc="upper left", framealpha=0.9)
ax.grid(axis="y", linestyle="--", alpha=0.5, zorder=1)
ax.set_ylim(0, counts.values.max() * 1.22)

plt.tight_layout()
plt.savefig(os.path.join(FIGS, "fig3_corpus_composition.png"))
plt.close()
print("  -> Saved fig3_corpus_composition.png")

# ============================================================================
# FIGURE 4 -- Treemap: E. coli Cluster Sizes
# ============================================================================
print("Figure 4 - E. coli Treemap...")

try:
    import squarify
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "squarify", "-q"])
    import squarify

ecoli_clusters = df_summary[df_summary["cluster_id"] >= 0].copy()
ecoli_counts = (
    df_claims[(df_claims["cluster_id"] >= 0) & (df_claims["organism"] == "E. coli")]
    .groupby("cluster_id").size().reset_index(name="ecoli_n"))
ecoli_clusters = ecoli_clusters.merge(ecoli_counts, on="cluster_id", how="left").fillna(0)
ecoli_clusters = (ecoli_clusters[ecoli_clusters["ecoli_n"] > 0]
                  .sort_values("ecoli_n", ascending=False))

labels_tm = [
    f"{SHORT_NAMES.get(r.cluster_id, str(r.cluster_id)).replace(chr(10), ' ')}\n({int(r.ecoli_n)})"
    for r in ecoli_clusters.itertuples()
]

norm = plt.Normalize(ecoli_clusters["ecoli_n"].min(), ecoli_clusters["ecoli_n"].max())
cmap = plt.cm.Blues
colors_tm = [cmap(0.35 + 0.60 * norm(v)) for v in ecoli_clusters["ecoli_n"]]

fig, ax = plt.subplots(figsize=(13, 7), facecolor=C_BG)
ax.set_facecolor(C_BG)

squarify.plot(
    sizes=ecoli_clusters["ecoli_n"].values,
    label=labels_tm,
    color=colors_tm,
    alpha=0.92,
    ax=ax,
    text_kwargs={
        "fontsize": 9.5, "fontweight": "bold", "color": "white",
        "path_effects": [pe.withStroke(linewidth=2, foreground="#1B3A5C")]
    })

ax.set_title(
    "E. coli Research Themes - Cluster Sizes\n"
    "(458 Clustered E. coli Explicit Justification Claims)",
    fontsize=14, fontweight="bold")
ax.axis("off")

sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, fraction=0.02, pad=0.01, shrink=0.7)
cbar.set_label("Number of E. coli Claims", fontsize=10)

plt.tight_layout()
plt.savefig(os.path.join(FIGS, "fig4_ecoli_treemap.png"))
plt.close()
print("  -> Saved fig4_ecoli_treemap.png")

# ============================================================================
# FIGURE 5 -- Publication-Quality UMAP Scatter
# ============================================================================
print("Figure 5 - UMAP scatter...")

df_plot  = df_claims[df_claims["cluster_id"] != -1].copy()
df_noise = df_claims[df_claims["cluster_id"] == -1].copy()

fig, ax = plt.subplots(figsize=(12, 8), facecolor="#0E1117")
ax.set_facecolor("#0E1117")

# noise (background, grey)
ax.scatter(df_noise["umap_x"], df_noise["umap_y"],
           c="#CCCCCC", s=6, alpha=0.18, zorder=1)

# clustered points by organism
for org, color in ORG_COLORS.items():
    mask = df_plot["organism"] == org
    ax.scatter(df_plot.loc[mask, "umap_x"], df_plot.loc[mask, "umap_y"],
               c=color, s=22, alpha=0.75, zorder=2, edgecolors="none", label=org)

# centroid cluster-ID badges
for cid in SHORT_NAMES:
    if cid < 0:
        continue
    sub = df_claims[df_claims["cluster_id"] == cid]
    if sub.empty:
        continue
    cx, cy = sub["umap_x"].mean(), sub["umap_y"].mean()
    ax.text(cx, cy, str(cid), fontsize=8.5, fontweight="bold",
            ha="center", va="center", color="white", zorder=5,
            bbox=dict(boxstyle="round,pad=0.25", facecolor="#1B6CA8",
                      edgecolor="none", alpha=0.85))

legend_handles = [
    Line2D([0], [0], marker="o", color="w", markerfacecolor=c,
           markersize=10, label=o)
    for o, c in ORG_COLORS.items()
] + [
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#CCCCCC",
           markersize=8, alpha=0.6, label="Noise (Cluster -1)")
]

ax.legend(handles=legend_handles, loc="lower right", fontsize=10,
          framealpha=0.2, facecolor="#1A1A2E", labelcolor="white")

ax.set_title(
    "Semantic Cluster Map - 2D UMAP Projection\n"
    "1,550 Clustered Claims from 2,037 Total (PubMedBERT Embeddings)",
    fontsize=13, fontweight="bold", color="white", pad=12)
ax.set_xlabel("UMAP Dimension 1", fontsize=11, color="#AAAAAA")
ax.set_ylabel("UMAP Dimension 2", fontsize=11, color="#AAAAAA")
ax.tick_params(colors="#777777")
for spine in ax.spines.values():
    spine.set_edgecolor("#333333")

plt.tight_layout()
plt.savefig(os.path.join(FIGS, "fig5_umap_publication.png"))
plt.close()
print("  -> Saved fig5_umap_publication.png")

# ============================================================================
# FIGURE 6 -- Network: Cluster -> Pathway
# ============================================================================
print("Figure 6 - Cluster-Pathway network...")

CLUSTER_PATHWAY_MAP = {
    0:  ("B.sub Spore &\nPhysiology",  ["BSU02020\n(Two-component)", "BSU00550\n(Cell wall)", "BSU02024\n(Sporulation)"]),
    1:  ("B.sub Model\nDefinition",    ["BSU02020\n(Two-component)"]),
    2:  ("Yeast\nEukaryotic Bio.",     ["SCE04111\n(Cell cycle)", "SCE04141\n(ER protein)", "SCE04011\n(MAPK)"]),
    3:  ("Genetic\nTractability",      ["SCE04111\n(Cell cycle)", "ECO03060\n(Sec secretion)"]),
    6:  ("Recombinant\nExpression",    ["ECO03060\n(Sec/Tat)", "ECO00650\n(Butanoate)"]),
    7:  ("Clinical\nPathogenesis",     ["MAP05130\n(ETEC infection)", "ECO00540\n(Lipid A)"]),
    9:  ("Antimicrobial\nScreening",   ["ECO01501\n(Beta-lactam)", "AcrAB-TolC\n(Efflux pump)"]),
   10:  ("DNA Replication\n& Repair",  ["ECO03030\n(DNA replication)", "ECO03430\n(MMR)", "ECO03440\n(HR)"]),
   11:  ("Bacterial Ref\nStandard",    ["ECO03060\n(Sec secretion)", "ECO03030\n(DNA replication)"]),
}

ORG_FOR_CLUSTER = {
    0: "B. subtilis", 1: "B. subtilis",
    2: "S. cerevisiae", 3: "S. cerevisiae",
    6: "E. coli", 7: "E. coli", 9: "E. coli", 10: "E. coli", 11: "E. coli",
}

G = nx.Graph()
pathway_nodes = set()
cluster_nodes = set()

for cid, (clabel, pathways) in CLUSTER_PATHWAY_MAP.items():
    cname = f"C{cid}"
    cluster_nodes.add(cname)
    G.add_node(cname, label=clabel, node_type="cluster",
               org=ORG_FOR_CLUSTER.get(cid, "E. coli"))
    for p in pathways:
        pathway_nodes.add(p)
        G.add_node(p, node_type="pathway")
        G.add_edge(cname, p)

pos = {}
pathway_list = sorted(pathway_nodes)
n_p = len(pathway_list)
for i, p in enumerate(pathway_list):
    angle = 2 * np.pi * i / n_p
    pos[p] = (2.6 * np.cos(angle), 2.6 * np.sin(angle))

cluster_list = sorted(cluster_nodes)
n_c = len(cluster_list)
for i, c in enumerate(cluster_list):
    angle = 2 * np.pi * i / n_c
    pos[c] = (1.1 * np.cos(angle), 1.1 * np.sin(angle))

fig, ax = plt.subplots(figsize=(13, 11), facecolor=C_BG)
ax.set_facecolor(C_BG)

nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.35, edge_color="#999999",
                       width=1.4, style="solid")

for cname in cluster_nodes:
    org = G.nodes[cname]["org"]
    color = ORG_COLORS[org]
    nx.draw_networkx_nodes(G, pos, nodelist=[cname], ax=ax,
                           node_color=color, node_size=1800, alpha=0.92)

nx.draw_networkx_nodes(G, pos, nodelist=list(pathway_nodes), ax=ax,
                       node_color=C_ACCENT, node_size=1100, alpha=0.85,
                       node_shape="s")

cluster_labels = {c: G.nodes[c]["label"] for c in cluster_nodes}
nx.draw_networkx_labels(G, pos, labels=cluster_labels, ax=ax,
                        font_size=6.5, font_weight="bold", font_color="white")

pathway_labels = {p: p for p in pathway_nodes}
nx.draw_networkx_labels(G, pos, labels=pathway_labels, ax=ax,
                        font_size=6.5, font_color="#333333")

legend_elems = [
    mpatches.Patch(color=C_ECOLI,    label="E. coli cluster"),
    mpatches.Patch(color=C_YEAST,    label="S. cerevisiae cluster"),
    mpatches.Patch(color=C_BACILLUS, label="B. subtilis cluster"),
    mpatches.Patch(color=C_ACCENT,   label="KEGG / EcoCyc Pathway"),
]
ax.legend(handles=legend_elems, loc="lower left", fontsize=10, framealpha=0.9)
ax.set_title(
    "Cluster - Biological Pathway Network\n"
    "(Justification Clusters Linked to KEGG / EcoCyc Database Pathways)",
    fontsize=13, fontweight="bold", pad=14)
ax.axis("off")

plt.tight_layout()
plt.savefig(os.path.join(FIGS, "fig6_cluster_pathway_network.png"))
plt.close()
print("  -> Saved fig6_cluster_pathway_network.png")

# ============================================================================
# FIGURE 7 -- Stacked Area: Temporal Shifts
# ============================================================================
print("Figure 7 - Stacked area chart...")

ecoli_df = df_claims[
    (df_claims["organism"] == "E. coli") & (df_claims["cluster_id"] >= 0)
].copy()

bins       = [1989, 1999, 2009, 2019, 2025]
# Plain ASCII hyphens only
labels_bins = ["1990-1999", "2000-2009", "2010-2019", "2020-2025"]
ecoli_df["decade"] = pd.cut(ecoli_df["year"], bins=bins, labels=labels_bins)
ecoli_df = ecoli_df.dropna(subset=["decade"])

pivot = ecoli_df.groupby(["decade", "cluster_id"]).size().unstack(fill_value=0)
pivot = pivot.div(pivot.sum(axis=1), axis=0) * 100
pivot = pivot.reindex(labels_bins).fillna(0)

ecoli_only_clusters = [c for c in pivot.columns if c in [4, 5, 6, 7, 8, 9, 10, 11, 12]]
pivot_ecoli = pivot[ecoli_only_clusters]

cluster_colors = [
    "#1B6CA8", "#2196D3", "#6EC6F0", "#F4A261", "#E76F51",
    "#D64045", "#2EAA6E", "#9C4F96", "#F2C14E"
]

x_pos = np.arange(len(labels_bins))

fig, ax = plt.subplots(figsize=(11, 7), facecolor=C_BG)
ax.set_facecolor(C_BG)

ax.stackplot(
    x_pos,
    [pivot_ecoli[c].values for c in ecoli_only_clusters],
    labels=[SHORT_NAMES[c].replace("\n", " ") for c in ecoli_only_clusters],
    colors=cluster_colors[:len(ecoli_only_clusters)],
    alpha=0.88)

ax.set_xticks(x_pos)
ax.set_xticklabels(labels_bins, fontsize=11)
ax.set_ylabel("Percentage of E. coli Explicit Claims (%)", fontsize=11)
ax.set_ylim(0, 100)
ax.set_title(
    "Temporal Shifts in E. coli Justification Themes\n(1990-2025, 4 Decade Bins)",
    fontsize=14, fontweight="bold")

handles, lbls = ax.get_legend_handles_labels()
ax.legend(handles[::-1], lbls[::-1],
          loc="center left", bbox_to_anchor=(1.01, 0.5),
          fontsize=9, framealpha=0.9, title="Research Theme", title_fontsize=9)

ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
plt.tight_layout()
plt.savefig(os.path.join(FIGS, "fig7_temporal_stacked_area.png"))
plt.close()
print("  -> Saved fig7_temporal_stacked_area.png")

# ============================================================================
# FIGURE 8 -- Radar Chart: Organism Research Profiles
# ============================================================================
print("Figure 8 - Radar chart...")

org_counts = (df_claims[df_claims["cluster_id"] >= 0]
              .groupby(["organism", "cluster_id"]).size().unstack(fill_value=0))
org_norm = org_counts.div(org_counts.sum(axis=1), axis=0) * 100

cats = [c for c in range(13) if c in org_norm.columns]
cat_labels = [SHORT_NAMES_RADAR.get(c, str(c)) for c in cats]
N = len(cats)

angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
angles += angles[:1]

fig = plt.figure(figsize=(11, 9), facecolor=C_BG)
ax = fig.add_axes([0.18, 0.10, 0.52, 0.52], projection="polar")
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
ax.set_xticklabels([])          # hide default tick labels — we draw our own
ax.set_rlabel_position(30)
ax.set_yticks([10, 20, 30, 40, 50, 60])
ax.set_yticklabels(["10%", "20%", "30%", "40%", "50%", "60%"],
                   fontsize=8, color="#888888")
ax.set_ylim(0, 65)
ax.grid(color="#CCCCCC", linestyle="--", linewidth=0.8)
ax.spines["polar"].set_color("#CCCCCC")

# ── Manually place horizontal labels outside the outermost ring ─────────────
LABEL_R = 76   # just beyond ylim=65
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

ax.legend(loc="upper left", bbox_to_anchor=(1.15, 1.0), fontsize=10, framealpha=0.9)
fig.suptitle(
    "Organism Research Profile Radar Chart\n"
    "Normalized Justification Distribution Across 13 Themes",
    fontsize=13, fontweight="bold", y=0.88)

plt.savefig(os.path.join(FIGS, "fig8_radar_organism_profiles.png"), dpi=300, bbox_inches="tight")

plt.close()
print("  -> Saved fig8_radar_organism_profiles.png")

# ============================================================================
# FIGURE 9 -- Redesigned Heatmap: Cross-Organism Comparison
# ============================================================================
print("Figure 9 - Redesigned heatmap...")

hmap_data = (df_claims[df_claims["cluster_id"] >= 0]
             .groupby(["organism", "cluster_id"]).size().unstack(fill_value=0))
hmap_norm = hmap_data.div(hmap_data.sum(axis=1), axis=0) * 100

org_order_h = ["E. coli", "S. cerevisiae", "B. subtilis"]
hmap_norm = hmap_norm.reindex([o for o in org_order_h if o in hmap_norm.index])

short_col_labels = [SHORT_NAMES.get(c, "?").replace("\n", "\n") for c in hmap_norm.columns]

fig, ax = plt.subplots(figsize=(16, 5), facecolor=C_BG)

sns.heatmap(
    hmap_norm,
    ax=ax,
    cmap="YlGnBu",
    annot=True,
    fmt=".1f",
    annot_kws={"size": 10, "weight": "bold"},
    linewidths=0.6,
    linecolor="#DDDDDD",
    cbar_kws={"label": "% of organism's clustered claims", "shrink": 0.7},
    xticklabels=short_col_labels,
    yticklabels=org_order_h)

ax.set_xticklabels(ax.get_xticklabels(), rotation=35, ha="right", fontsize=9)
ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=11, fontweight="bold")
ax.set_xlabel("Justification Cluster Theme", fontsize=11, labelpad=10)
ax.set_ylabel("")
ax.set_title(
    "Cross-Organism Justification Profile Matrix\n"
    "Normalized Percentage of Each Organism's Claims Across 13 Semantic Clusters",
    fontsize=13, fontweight="bold", pad=14)

# blue border on E. coli row (row index 0)
for col_idx in range(hmap_norm.shape[1]):
    ax.add_patch(plt.Rectangle(
        (col_idx, 0), 1, 1,
        fill=False, edgecolor=C_ECOLI, lw=2.0, clip_on=False))

plt.tight_layout()
plt.savefig(os.path.join(FIGS, "fig9_heatmap_redesigned.png"))
plt.close()
print("  -> Saved fig9_heatmap_redesigned.png")

# ============================================================================
print("\n[OK] All 9 figures saved to:", FIGS)
for f in sorted(os.listdir(FIGS)):
    if f.endswith(".png"):
        size_kb = os.path.getsize(os.path.join(FIGS, f)) // 1024
        print(f"   {f:<50}  {size_kb:>6} KB")
