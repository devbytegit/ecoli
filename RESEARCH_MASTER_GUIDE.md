# Research Master Guide · Computational Microbiology
## Why Is Escherichia coli the Premier Model Microorganism?
A complete step-by-step guide to executing an LLM-augmented computational microbiology research study — from data collection to published paper.

*   **Researcher:** Olufisayo Timileyin Emmanuel
*   **Corpus:** 3,273 Papers · 1990–2025
*   **Pipeline:** 6 Phases
*   **Status:** **All 6 Computational Phases Completed** (Next: Paper Writing & Submission)

---

## Overview

### Section 01: What This Research Is About
Every microbiology student learns that *E. coli* is the premier model microorganism. But the scientific justification has always been qualitative — textbook claims, academic tradition, and anecdotal consensus. Nobody has ever measured it computationally. This research does exactly that.

*   **🔬 The core idea:** Use an LLM pipeline to read 3,273 scientific papers, extract why scientists say they use *E. coli*, cluster those reasons computationally, map them to biology, and compare across other model microorganisms — all to answer the question nobody has answered with data.
*   **⚡ Your unique edge:** You can build the pipeline (ML engineering) AND interpret the biology (First Class Microbiology). That intersection is rare and is the reason this paper is publishable.

---

## Aim & Objectives

### Section 02: Aim & Objectives
#### Research Aim
To computationally investigate the biological, technical, and historical properties that have established *Escherichia coli* as the premier model microorganism in microbiology and molecular biology, through the application of large language model-augmented literature mining, semantic clustering, and cross-organism comparative analysis across four decades of peer-reviewed scientific literature.

*   **OBJ 1 (Dataset Construction):** Collect and curate peer-reviewed abstracts (1990–2025) from PubMed explicitly referencing *E. coli* as a model microorganism, yielding 2,051 *E. coli*, 950 *S. cerevisiae*, and 272 *B. subtilis* papers after deduplication and filtering.
*   **OBJ 2 (Claim Extraction):** Build an LLM pipeline that reads each abstract and extracts the specific reasons authors give for using the organism as their model microorganism, outputting strict JSON with hallucination guards.
*   **OBJ 3 (Clustering):** Group extracted reasons into meaningful thematic categories using PubMedBERT sentence embeddings and HDBSCAN unsupervised clustering.
*   **OBJ 4 (Biological Mapping):** Link each thematic cluster to established biological systems and pathways using the KEGG and EcoCyc databases.
*   **OBJ 5 (Temporal Analysis):** Track how scientific justification for *E. coli*'s premier status has shifted across four decades from 1990 to 2025.
*   **OBJ 6 (Comparative Analysis):** Compare *E. coli* justification claims against *S. cerevisiae* and *B. subtilis*, identifying what uniquely elevates *E. coli* to premier standing. All cross-organism comparisons reported as percentages.

---

## Research Questions

### Section 03: Research Questions
*   **RQ1 — Primary:** Is *Escherichia coli*'s status as the premier model microorganism driven primarily by biological properties, or do economic, historical, and cultural factors play equally significant roles?
*   **RQ2 — Clustering:** What are the principal thematic categories of scientific justification for *E. coli*'s premier model microorganism status as revealed by computational analysis of peer-reviewed literature?
*   **RQ3 — Temporal:** Is *Escherichia coli* still statistically the premier model microorganism in current scientific literature, or do emerging trends suggest a shift toward other microorganisms?
*   **RQ4 — Comparative:** What properties uniquely distinguish *E. coli* from *S. cerevisiae* and *B. subtilis* in the scientific literature, and how do these distinctions quantitatively support its premier standing?
*   **RQ5 — Systems Biology:** To which biological systems and molecular pathways do the most frequently cited properties of *E. coli* map, revealing its systemic tractability as a model microorganism?

---

## The 6-Phase Research Pipeline

### Section 04: Pipeline Execution Status
Every phase builds on the previous one. Each phase has a clearly defined input, process, and output.

```
[P1: Data Collection] ──(Done)──> [P2: Claim Extraction] ──(Done)──> [P3: Semantic Clustering] ──(Done)──> [P4: Biological Mapping] (Done)
                                                                                                                   │
[P6: Comparative Analysis] <──(Done)── [P5: Temporal Analysis] <──(Done)───────────────────────────────────────────┘
```

#### P1: Data Collection
*   **Status:** **Completed ✓**
*   **Process:** Query PubMed using 7 Boolean search strings (5 for *E. coli*, 1 each for comparison organisms) from 1990–2025. Deduplicate and filter (English, journal articles, abstracts available).
*   **Tools:** Biopython Entrez, pandas, PubMed API (`script.py`).
*   **Output:** `data/raw/corpus_raw.csv` — **3,273 unique papers** (*E. coli*: 2,051 | *S. cerevisiae*: 950 | *B. subtilis*: 272).

#### P2: LLM Claim Extraction
*   **Status:** **Completed ✓**
*   **Process:** Sends each abstract to LLM (Llama 3.3 70B / gpt-oss-120b via Groq/Cerebras). Returns JSON: `claim`, `category` (biological/technical/historical/economic/cultural), `subcategory`, `supporting_quote`. Quote verified against abstract using fuzzy matching ($\ge$ 0.65). Hallucination rate evaluated at a very low 0.21% (7 claims removed).
*   **Tools:** Groq/Cerebras APIs, jsonschema, tenacity, `phase2_extract.py`, `cleanup_phase2.py`.
*   **Key Results:**
    *   **The Axiomatic Acceptance Finding:** Across the corpus, 50.2% of papers have no explicit justification. For *E. coli* alone, **61.5% of papers contain no justification** (treated as a self-evident axiom), compared to only ~31% for Yeast and ~32% for Bacillus.
*   **Output:** `data/processed/phase2_claims_clean.csv` (3,680 clean claims) and `data/processed/phase3_input.csv` (2,037 explicit justification claims).

#### P3: Embedding & Clustering
*   **Status:** **Completed ✓**
*   **Process:** Encode the 2,037 explicit claims using PubMedBERT. Reduce dimensionality to 10D using UMAP (cosine metric) for HDBSCAN clustering. Optimize parameters using grid search (`min_cluster_size=15`, `min_samples=15`). Found **13 distinct clusters** with a Silhouette score of **0.5388** and 23.91% noise. Assigned descriptive scientific names to all 13 clusters.
*   **Tools:** sentence-transformers, PubMedBERT, HDBSCAN, UMAP, scikit-learn, matplotlib, seaborn, `phase3_cluster.py`.
*   **Outputs:**
    *   `data/processed/phase3_embeddings.npy` (embeddings matrix).
    *   `data/processed/phase3_clustered_claims.csv` (claims with cluster IDs and coordinates).
    *   `data/processed/phase3_cluster_summary.csv` (statistics and exemplars for all 13 clusters).
    *   `data/figures/phase3_umap_clusters.png` (2D projection scatter plot).
    *   `data/figures/phase3_cluster_distribution.png` (organism stacked bar chart).

#### P4: Biological Pathway Mapping
*   **Status:** **Completed ✓**
*   **Process:** Connect each cluster's biology to databases.
    *   For the 9 *E. coli*-dominant clusters (Clusters 4–12), read representative claims.
    *   Query KEGG API to find pathway maps (e.g., mismatch repair, Sec secretion, central metabolism).
    *   Query EcoCyc/MetaCyc to find gene networks and metabolic pathways.
    *   Draft automated mapping via LLM, then verify manually to build the final pathway lookup table.
*   **Tools:** KEGG API, EcoCyc, LLM verification, Obsidian vault.
*   **Output:** [phase4_pathway_map.csv](file:///c:/Users/olufi/Desktop/QUICK%20FILES/ECOLI/data/processed/phase4_pathway_map.csv) (mapping clusters to biological systems, KEGG IDs, and EcoCyc pathways). Documented in [[phase4_mapping|Phase 4: Biological Mapping]].

#### P5: Temporal Analysis
*   **Status:** **Completed ✓**
*   **Process:** Stratify *E. coli* claims (867 claims) by decade bins: 1990–1999, 2000–2009, 2010–2019, 2020–2025. Calculate frequency percentages and plot shifts in scientific justifications across time (e.g., tracking the rise of systems biology/reference standards and the decline of DNA replication/repair).
*   **Tools:** pandas, matplotlib, seaborn.
*   **Output:** [phase5_temporal_trends.csv](file:///c:/Users/olufi/Desktop/QUICK%20FILES/ECOLI/data/processed/phase5_temporal_trends.csv) and [phase5_temporal.png](file:///c:/Users/olufi/Desktop/QUICK%20FILES/ECOLI/data/figures/phase5_temporal.png). Documented in [[phase5_temporal|Phase 5: Temporal Analysis]].

#### P6: Cross-Organism Comparative Analysis
*   **Status:** **Completed ✓**
*   **Process:** Compare the cluster distributions across the three organisms as percentages to quantify *E. coli*'s unique functional profile (spanning 9 clusters) against the narrow profiles of *S. cerevisiae* (2 clusters) and *B. subtilis* (2 clusters). Plot as a comparative heatmap.
*   **Tools:** pandas, seaborn heatmap.
*   **Output:** [phase6_comparison.csv](file:///c:/Users/olufi/Desktop/QUICK%20FILES/ECOLI/data/processed/phase6_comparison.csv) and heatmap [phase6_comparison_heatmap.png](file:///c:/Users/olufi/Desktop/QUICK%20FILES/ECOLI/data/figures/phase6_comparison_heatmap.png). Documented in [[phase6_comparison|Phase 6: Comparative Analysis]].

---

## Technical Setup & Data

### Section 05: Environment Setup
All required packages are installed in the local virtual environment `.venv/`:
```bash
pip install biopython pandas tqdm openai tenacity jsonschema python-dotenv
pip install sentence-transformers hdbscan umap-learn matplotlib seaborn scikit-learn pytest
```

| API / Service | Purpose | Cost | Status |
| :--- | :--- | :--- | :--- |
| **NCBI/PubMed** | Phase 1 collection | Free | Configured (Entrez email in `.env`) |
| **Groq / Cerebras** | Phase 2 claim extraction | Free/Paid | Configured (API keys in `.env`) |
| **HuggingFace** | Phase 3 PubMedBERT | Free | Model cached locally (`S-PubMedBert-MS-MARCO`) |
| **KEGG API** | Phase 4 pathway mapping | Free | rest.kegg.jp |
| **EcoCyc** | Phase 4 E. coli mapping | Free | ecocyc.org |

### Section 06: The Corpus — Final Numbers
*   **3,273** Total unique papers in corpus
*   **2,051** *E. coli* papers
*   **950** *S. cerevisiae* papers
*   **272** *B. subtilis* papers
*   **35 Years** Covered (1990–2025)
*   **📋 Normalization Rule:** All cross-organism comparisons in the paper are reported as percentages, not raw counts, to account for differences in corpus sizes (2,051 vs. 950 vs. 272).

---

## Publication Plan

### Section 07: Paper Structure
*   **Paper Title:** *"Beyond Convention: A Computational Analysis of the Biological, Technical, and Historical Properties Driving Escherichia coli's Premier Status as a Model Microorganism"*
*   **Structure:**
    *   **§ 1 Abstract:** 200–250 words summarizing the computational methodology and key findings (e.g. the 61.5% axiomatic null rate and 13 semantic clusters).
    *   **§ 2 Introduction:** Setting the history, the qualitative consensus gap, and introducing the 5 Research Questions.
    *   **§ 3 Methodology:** Subsection per phase (3.1 Data Collection $\rightarrow$ 3.6 Comparative Analysis).
    *   **§ 4 Results:** Raw dataset overview, claim extraction counts, 13 clusters + UMAP plot, KEGG/EcoCyc pathway map, temporal line/bar charts, and cross-organism heatmap.
    *   **§ 5 Discussion:** Answering the RQs directly. Exploring biological vs. cultural drivers (61.5% acceptance gap), the architecture of E. coli's multifaceted premier status, its comparison to eukaryotic/Gram-positive models, study limitations, and future steps.
    *   **§ 6 Conclusion:** Restatement of aim and broader significance.
    *   **§ S Supplementary Materials:** Full PubMed Boolean queries, LLM JSON schema, cluster membership lists, and link to GitHub code.

### Section 08: Target Journals
1.  **mSystems (ASM):** Systems biology in microbiology — direct field match, high impact (🥇 First choice).
2.  **PLOS ONE:** Computational + biology, open access, rigorous, broad readership (🥈 Second choice).
3.  **Frontiers in Microbiology:** Direct field match, open access, fast review cycle (🥉 Third choice).
4.  **BMC Bioinformatics:** Computational methods focus (Backup).

### Section 09: Chronological Timeline
*   **Phase 1 (Data Collection):** Done ✓ (corpus built and verified).
*   **Phase 2 (LLM Claim Extraction):** Done ✓ (hallucinations removed, 50.2% overall null split identified, 61.5% E. coli axiomatic null rate).
*   **Phase 3 (Clustering & Naming):** Done ✓ (PubMedBERT vectors, 13 clusters generated, Silhouette score 0.5388, descriptive names assigned).
*   **Phase 4 (Biological Mapping):** Done ✓ (Mapped the 13 clusters to KEGG and EcoCyc, saved to [phase4_pathway_map.csv](file:///c:/Users/olufi/Desktop/QUICK%20FILES/ECOLI/data/processed/phase4_pathway_map.csv), documented in [[phase4_mapping]]).
*   **Phase 5 (Temporal Analysis):** Done ✓ (Decade-by-decade shifts, saved to [phase5_temporal_trends.csv](file:///c:/Users/olufi/Desktop/QUICK%20FILES/ECOLI/data/processed/phase5_temporal_trends.csv) and [phase5_temporal.png](file:///c:/Users/olufi/Desktop/QUICK%20FILES/ECOLI/data/figures/phase5_temporal.png), documented in [[phase5_temporal]]).
*   **Phase 6 (Comparative Analysis):** Done ✓ (Cross-organism comparison matrix and heatmap, saved to [phase6_comparison.csv](file:///c:/Users/olufi/Desktop/QUICK%20FILES/ECOLI/data/processed/phase6_comparison.csv) and [phase6_comparison_heatmap.png](file:///c:/Users/olufi/Desktop/QUICK%20FILES/ECOLI/data/figures/phase6_comparison_heatmap.png), documented in [[phase6_comparison]]).
*   **Writing & Submission:** **Current Step** (Weeks 4–8: Writing methods, results, and discussion sections).

---

## Second Brain (Obsidian Vault `ecoli_brain/`)

The Obsidian vault tracks all qualitative reasoning and updates alongside the pipeline execution.

```
E. coli Premier Study/
├── index.md                 # Master directory of pages
├── log.md                   # Append-only chronological log
├── aim_and_objectives.md    # Aim, objectives, and research questions
├── methodology.md           # All 6 phases documented
├── phase1_collection.md     # Phase 1 dataset summary
├── phase2_extraction.md     # Phase 2 extraction results and 50/50 split
├── phase3_clustering.md     # Phase 3 HDBSCAN clusters and names table
├── organisms/
│   ├── e_coli.md            # E. coli profile & 9 clusters
│   ├── s_cerevisiae.md      # Yeast profile & 2 eukaryotic clusters
│   └── b_subtilis.md        # B. subtilis profile & 2 Gram-positive clusters
├── raw/
│   └── sources/             # Immutable transcripts and chat history
└── Clusters/                # (To be filled in Phase 4)
    ├── Cluster_0.md         # Gram-Positive Physiology pathways
    ├── Cluster_2.md         # Eukaryotic Cell Biology pathways
    └── ...
```

*   **📓 Daily Log Habit (Karpathy Method):** We append an entry to `log.md` for every session worked. This log preserves methods memory and simplifies paper writing during the final weeks.
