# 3. Methodology

This study employs an LLM-augmented computational literature-mining and machine learning pipeline to analyze the scientific justifications driving the selection of model microorganisms. The methodology is executed in six distinct computational phases:

```
[Phase 1: Dataset Construction]
               │
[Phase 2: LLM Claim Extraction & Cleaning]
               │
[Phase 3: Semantic Embedding & Clustering (UMAP + HDBSCAN)]
               │
[Phase 4: Biological Pathway Database Mapping (KEGG + EcoCyc)]
               │
[Phase 5: Temporal Trend Analysis (1990–2025)]
               │
[Phase 6: Cross-Organism Comparative Profile Analysis]
```

---

## 3.1 Phase 1: Dataset Construction

Scientific paper abstracts and metadata were retrieved from the NCBI PubMed database using the Biopython Entrez API. The search was scoped to peer-reviewed journal articles published in English between January 1, 1990, and December 31, 2025. 

To collect literature where organisms are explicitly used as model systems, seven Boolean search queries were designed. Five queries targeted the primary subject *Escherichia coli*, and one query each targeted the eukaryotic comparison organism *Saccharomyces cerevisiae* and the Gram-positive bacterial comparison organism *Bacillus subtilis*:

*   **E. coli Queries:**
    1.  `("Escherichia coli"[Title/Abstract] AND "model organism"[Title/Abstract])`
    2.  `("Escherichia coli"[Title/Abstract] AND "model system"[Title/Abstract])`
    3.  `("E. coli"[Title/Abstract] AND "model organism"[Title/Abstract])`
    4.  `("Escherichia coli"[Title/Abstract] AND "model bacterium"[Title/Abstract])`
    5.  `("Escherichia coli"[Title/Abstract] AND "reference organism"[Title/Abstract])`
*   **S. cerevisiae Query:**
    6.  `("Saccharomyces cerevisiae"[Title/Abstract] AND "model organism"[Title/Abstract])`
*   **B. subtilis Query:**
    7.  `("Bacillus subtilis"[Title/Abstract] AND "model organism"[Title/Abstract])`

All retrieved records were deduplicated across search queries using their PubMed ID (PMID). Records lacking abstract texts or containing abstracts shorter than 30 characters were discarded. The final curated corpus consisted of **3,273 unique papers** (2,051 *E. coli* papers, 950 *S. cerevisiae* papers, and 272 *B. subtilis* papers).

---

## 3.2 Phase 2: LLM-Driven Claim Extraction & Cleaning

To isolate the specific justifications scientists give for using their chosen model organism, an LLM extraction pipeline was built using the gpt-oss-120b model queried via the Cerebras Inference API. 

### 3.2.1 Extraction Schema and Prompting
Each abstract in the corpus was processed individually. The model was instructed to return a structured JSON object strictly matching the following schema:
*   `explicit_reason_found` (boolean): `true` if the abstract explicitly states a reason/justification for using the organism; `false` otherwise.
*   `justification_claims` (array of objects): Contains the extracted `claim` (paraphrased), `category` (constrained to `biological`, `technical`, `historical`, `economic`, or `cultural`), `subcategory` (a short thematic tag), and `supporting_quote` (the verbatim text from the abstract).
*   `null_reason` (string or null): Documented rationale if `explicit_reason_found` is `false`.

### 3.2.2 Anti-Hallucination Guardrails
To prevent model hallucinations, a 5-layer quality assurance pipeline was implemented:
1.  **Deterministic Temperature:** `temperature = 0.0` was enforced to eliminate creative token generation.
2.  **Explicit Null Rule:** The model was strictly instructed to return `false` for `explicit_reason_found` and `null` for claims if no direct text justified the organism, preventing logical inferences.
3.  **Fuzzy Quote Verification:** Every extracted `supporting_quote` was matched against the raw abstract text using a sliding-window character comparison (`difflib.SequenceMatcher`). Quotes failing to achieve a similarity ratio $\ge 0.65$ were flagged and discarded.
4.  **Schema and ID Validation:** Outputs were validated programmatically using the `jsonschema` library.
5.  **Progressive Cache Saving:** API outputs were saved progressively to JSONL files to allow resuming and protect against mid-run network interruptions.

Following extraction, `cleanup_phase2.py` was executed to filter out hallucinated entries (removing 7 claims, representing a low 0.21% hallucination rate) and isolate the explicit justification claims. This resulted in a clean explicit justification dataset of **2,037 claims** (867 *E. coli*, 944 *S. cerevisiae*, and 226 *B. subtilis*) for clustering.

---

## 3.3 Phase 3: Semantic Embedding & Clustering

The 2,037 explicit justification claims were converted into dense vectors using the pre-trained `pritamdeka/S-PubMedBert-MS-MARCO` SentenceTransformer model, yielding 768-dimensional embeddings tailored for biomedical text semantics.

To resolve the "curse of dimensionality" during density-based clustering, a two-step dimensionality reduction workflow was implemented:
1.  **For Clustering:** Embeddings were projected into **10 dimensions** using UMAP (cosine metric, `n_neighbors=15`, `random_state=42`) to preserve local and global semantic structures.
2.  **For Visualization:** Embeddings were separately projected to **2 dimensions** solely to generate cluster scatter plots.

Density-based clustering was performed on the 10D vectors using HDBSCAN. To find the optimal cluster resolution, a grid-search optimization sweep was conducted over HDBSCAN hyper-parameters (`min_cluster_size` ranging from 10 to 30, `min_samples` from 3 to 15). The grid search optimized for the maximum Silhouette score (excluding noise points) while keeping the outlier (noise) rate below 30% and yielding between 8 and 18 clusters. 

The optimal configuration selected was `min_cluster_size=15` and `min_samples=15`. This returned **13 distinct clusters** (Cluster 0 to 12) with a Silhouette score of **0.5388** and a noise/outlier rate of **23.91%** (487 out of 2,037 claims marked as Cluster -1).

To identify the core concept of each cluster, the centroid of each cluster's member embeddings in the 10-dimensional space was calculated, and claims were ranked by their Euclidean distance to their respective cluster centroid. The top 10 closest claims were extracted as "exemplars" to guide thematic naming.

---

## 3.4 Phase 4: Biological Pathway Database Mapping

The biological justifications of the 13 clusters were mapped to physical biological pathways and systems. The **KEGG REST API** (rest.kegg.jp) was queried to retrieve pathway IDs and descriptions for the three host organisms:
*   *Escherichia coli* K-12 MG1655 (`eco`)
*   *Saccharomyces cerevisiae* (`sce`)
*   *Bacillus subtilis* 168 (`bsu`)

A cross-reference dictionary was compiled where clusters were associated with corresponding KEGG pathways (e.g. DNA replication `eco03030`, mismatch repair `eco03430`, or protein export `eco03060`). For *E. coli*-dominant clusters (Clusters 4–12), claims were additionally cross-referenced with curated gene networks and metabolic pathways in the **EcoCyc Database** (ecocyc.org) to obtain high-resolution systems biology annotations. Mappings were verified and saved as `data/processed/phase4_pathway_map.csv`.

---

## 3.5 Phase 5: Temporal Trend Analysis

The 458 clustered *E. coli* claims (excluding noise) were binned across a 35-year timeline by publication years into four periods:
*   **Bin 1:** 1990–1999 (39 claims)
*   **Bin 2:** 2000–2009 (98 claims)
*   **Bin 3:** 2010–2019 (184 claims)
*   **Bin 4:** 2020–2025 (137 claims)

For each decade bin, the relative frequency (percentage representation) of each *E. coli* cluster within that era's explicit claims was calculated. Relative frequencies were utilized instead of raw counts to normalize for the growing volume of scientific literature over time. The trajectories of the individual research themes were modeled using line plots and stacked bar charts. This decadal shift corresponds directly with the completion of the *E. coli* genome sequencing in 1997 `[3]`.

---

## 3.6 Phase 6: Cross-Organism Comparative Profile Analysis

To contrast *E. coli*'s justification profile against *S. cerevisiae* and *B. subtilis*, the normalized distribution of each organism's total clustered claims across the 13 themes was computed. 

For each organism, the counts of claims in each cluster were divided by that organism's total number of clustered claims (458 *E. coli*, 880 *S. cerevisiae*, and 212 *B. subtilis* claims, excluding noise). This column-wise normalization allowed the evaluation of the breadth of each model organism's research profile independently of the size differences in their starting corpora. The comparison matrix was plotted as an annotated heatmap to visualize niche specialization and multi-dimensional dominance.
