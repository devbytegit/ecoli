# 4. Results

This section presents the empirical and quantitative results generated across the six phases of the computational literature-mining and clustering pipeline.

---

## 4.1 Dataset Composition and General Characteristics

Following literature retrieval, deduplication, and quality-filtering in Phase 1, the final text corpus comprised **3,273 unique peer-reviewed papers** containing English abstracts published between 1990 and 2025. The distribution of papers across the three target model microorganisms was:
*   ***Escherichia coli* (Subject):** 2,051 papers (62.7% of the total corpus)
*   ***Saccharomyces cerevisiae* (Eukaryotic Control):** 950 papers (29.0%)
*   ***Bacillus subtilis* (Gram-Positive Control):** 272 papers (8.3%)

The timeline of the dataset spanned 35 years, with the publication volume showing a steady upward trajectory: 255 papers in 1990–1999, 652 papers in 2000–2009, 1,422 papers in 2010–2019, and 944 papers in 2020–2025 (visualized in Figure 3, data/figures/fig3_corpus_composition.png).

---

## 4.2 Justification Extraction and the Axiomatic Acceptance Gap

Phase 2 evaluated the 3,273 abstracts using LLM-based structured extraction to determine if authors explicitly explained why they chose their model organism.

### 4.2.1 The Overall Corpus Split
Across all three organisms, the corpus was split almost equally between papers containing explicit justifications and those treating the choice as an implicit assumption:
*   **Explicit Reason Found:** 1,626 papers (49.7% of the processed corpus; visualized in Figure 2, data/figures/fig2_ecoli_donut.png)
*   **Null (No Reason Stated):** 1,643 papers (50.3% of the processed corpus)

### 4.2.2 The Axiomatic Acceptance Gap (RQ1 Answer)
*   ***Escherichia coli*:** **61.6% Null** [95% CI: 59.5%–63.7%] (1,263 out of 2,051 papers contain no justification; only 788 papers explicitly justify its use).
*   ***Saccharomyces cerevisiae*:** **31.2% Null** [95% CI: 28.2%–34.1%] (296 out of 950 papers contain no justification; 654 papers explicitly justify its use).
*   ***Bacillus subtilis*:** **32.4% Null** [95% CI: 26.8%–37.9%] (88 out of 272 papers contain no justification; 184 papers explicitly justify its use).

To test whether the difference in justification rates across the three organisms is statistically significant, a Chi-square test of independence was performed on the $3 \times 2$ contingency table of organism versus justification status (implicit vs. explicit). The difference was found to be highly significant ($\chi^2(2) = 278.68$, $p < 0.0001$, raw $p = 3.06 \times 10^{-61}$).

This **Axiomatic Acceptance Gap** indicates that in nearly two-thirds (61.6%) of *E. coli* publications, the model status of the bacterium is treated as a self-evident axiom requiring no validation. In contrast, researchers using Yeast and Bacillus feel compelled to explicitly justify their model choice in more than two-thirds of their papers (~68.8% and ~67.6% respectively, visualized in Figure 1, data/figures/fig1_axiomatic_acceptance_gap.png). 

After removing 7 claims flagged by fuzzy quote verification (0.21% hallucination rate), the papers with explicit justifications yielded a clean dataset of **2,037 explicit claims** (867 *E. coli*, 944 *S. cerevisiae*, and 226 *B. subtilis*) for clustering.

---

## 4.3 Thematic Justification Clusters (RQ2 Answer)

Unsupervised density-based clustering (HDBSCAN) of the 2,037 PubMedBERT embeddings in the 10D UMAP space identified **13 distinct clusters** (Cluster 0 to 12) representing primary themes of scientific justification. A total of 487 claims (23.91%) were classified as noise (outliers, Cluster -1). The Silhouette score of the clustered points was **0.5388**, confirming robust semantic separation. 

Table 4.1 summarizes the size, dominant organism, dominant category, and representative exemplar claims for the 13 clusters. The spatial separation of the semantic clusters is projected in 2D UMAP space (Figure 5, data/figures/fig5_umap_publication.png). Additionally, Figure 4 (data/figures/fig4_ecoli_treemap.png) provides a treemap of E. coli's explicit justifications across the 9 dominant E. coli themes, showing the relative size and share of each category.

### Table 4.1: Thematic Cluster Analysis Summary

| Cluster ID | Theme Name | Size | Dom. Organism (%) | Dom. Category | Exemplar Claim (Closest to Centroid) |
| :---: | :--- | :---: | :--- | :--- | :--- |
| **0** | Gram-Positive Physiology, Endospore Formation, and Industrial Bioprocessing (B. subtilis) | 166 | *B. subtilis* (88.6%) | biological | *"B. subtilis is used because it serves as a model organism for Gram-positive spore-forming bacteria"* |
| **1** | Gram-Positive Bacterium Model Definition | 29 | *B. subtilis* (82.8%) | biological | *"It is a model organism of Gram-positive bacteria"* |
| **2** | Eukaryotic Cell Biology, Conserved Metabolic Pathways, and Human Disease Modeling (S. cerevisiae) | 530 | *S. cerevisiae* (98.5%) | biological | *"Yeast is used because it serves as a model organism for studying genetic mechanisms that are difficult to investigate in mammalian cells"* |
| **3** | Genetic Tractability, Molecular Tooling, and Industrial Cell Factories | 433 | *S. cerevisiae* (80.6%) | biological | *"Vast knowledge accumulated over decades of research"* |
| **4** | Experimental Rationale for Organism Selection (E. coli) | 25 | *E. coli* (100.0%) | biological | *"E. coli was chosen because it is a model bacterium"* |
| **5** | Standard Model Bacterium Utility and Characterization (E. coli) | 40 | *E. coli* (100.0%) | biological | *"E. coli is used because it is a well-established model bacterium"* |
| **6** | Heterologous Protein Expression and Recombinant Production Chassis (E. coli) | 64 | *E. coli* (92.2%) | technical | *"E. coli was used as a host for producing purified transducible Cre protein"* |
| **7** | Clinical Pathogenesis, Virulence Modeling, and Infectious Disease (E. coli) | 55 | *E. coli* (96.4%) | biological | *"E. coli is associated with human diarrheal disease, making it relevant for study"* |
| **8** | Gram-Negative Reference Organism and Cell Envelope Modeling (E. coli) | 24 | *E. coli* (100.0%) | biological | *"E. coli is used as a representative model organism for Gram-negative bacteria"* |
| **9** | Antimicrobial Screening, Drug Tolerance, and Resistance Mechanisms (E. coli) | 28 | *E. coli* (100.0%) | biological | *"E. coli is used as a model organism for studying antibiotic responses"* |
| **10** | DNA Replication, Recombination, Repair, and Replication Fidelity (E. coli) | 29 | *E. coli* (93.1%) | biological | *"E. coli is used as a model system for studying chromosomal replication fidelity"* |
| **11** | Bacterial Reference Standard and Legacy Model Characterization (E. coli) | 101 | *E. coli* (99.0%) | biological | *"E. coli is a well-established model organism for studying cellular behavior"* |
| **12** | Genomic Annotation and Molecular Genetics Reference (E. coli) | 26 | *E. coli* (100.0%) | historical | *"E. coli is used as a model organism"* |

---

## 4.4 Biological Pathway Database Mapping (RQ5 Answer)

Phase 4 mapped the 13 clusters to physical biological pathways and regulatory networks (visualized as a network mapping in Figure 6, data/figures/fig6_cluster_pathway_network.png). Mappings were verified against KEGG pathway models (`eco`, `sce`, `bsu`) and the EcoCyc database:

*   **Gram-Positive Regulation (Clusters 0 & 1):** Map to sporulation quorum sensing and two-component systems (`bsu02020`, `bsu02024`) and cell wall synthesis (`bsu00550`).
*   **Eukaryotic Cellular Mechanics (Cluster 2):** Maps to cell cycle/meiosis controls (`sce04111`, `sce04113`), endoplasmic reticulum protein processing (`sce04141`), and MAPK signaling (`sce04011`).
*   **Molecular Recombinant Host (Cluster 6):** Maps to inner membrane translocation systems—the Sec secretion system and Twin-Arginine Translocation (Tat) system (`eco03060` / EcoCyc: Sec pathway, Tat system).
*   **Medically Relevant Infection (Cluster 7):** Maps to `map05130` (Pathogenic E. coli infection), focusing on fimbriae adhesion, pili assembly, and Lipid A biosynthesis (`eco00540`).
*   **Antibiotic Assays (Cluster 9):** Maps to beta-lactam resistance (`eco01501`) and the AcrAB-TolC multidrug efflux pump (EcoCyc: AcrAB-TolC efflux).
*   **Replication Fidelity (Cluster 10):** Maps to the DNA replication fork machinery (`eco03030`), methyl-directed mismatch repair (`eco03430`), and homologous recombination (`eco03440` / EcoCyc: RecBCD pathway).

---

## 4.5 Temporal Justification Trajectories (RQ3 Answer)

Phase 5 tracked shifts in the justification for using *E. coli* over time. The 458 clustered *E. coli* explicit claims were binned into four decadal periods. The temporal trajectories (visualized as a stacked area chart in Figure 7, data/figures/fig7_temporal_stacked_area.png) revealed three major shifts:

1.  **Rise of the "Bacterial Reference Standard":** Justifications selecting E. coli as the definitive bacterial reference standard rose continuously from **2.9% in the 1990s** to **26.0% in the 2000s**, reaching **30.3% in the 2020s**. This corresponds directly with the completion of the *E. coli* genome sequencing in 1997.
2.  **Decline of "DNA Replication & Repair":** Claims based on E. coli DNA replication fork and repair mechanics fell continuously from **20.6% in the 1990s** to just **2.5% in the 2020s**, reflecting the transition of molecular genetics research toward eukaryotic hosts.
3.  **Normalization of Heterologous Expression:** Claims based on *Heterologous Expression Host* utility dropped sharply from **44.1% in the 1990s** to **14.3% in the 2000s** and **12.6% in the 2020s**, showing that protein expression has become an implicit utility requiring less explicit justification.

---

## 4.6 Cross-Organism Comparative Profile Analysis (RQ4 Answer)

Phase 6 normalized the cluster frequencies for each organism to compare their scientific profiles. The relative specialization of each organism is illustrated via a radar chart profile (Figure 8, data/figures/fig8_radar_organism_profiles.png), and the normalized distribution of justification themes is compared in the cross-organism comparative matrix heatmap (Figure 9, data/figures/fig9_heatmap_redesigned.png), showing that:
*   **S. cerevisiae (Yeast)** is a highly specialized model, with **99.0%** of its justifications concentrated in just **two themes**: *Eukaryotic Biology & Disease Modeling* (59.3%) and *Genetic Tractability & Workhorse Tools* (39.7%).
*   **B. subtilis** is similarly specialized, with **98.1%** of justifications concentrated in just **three themes**: *Gram-Positive Physiology & Bioprocess* (69.3%), *Genetic Tractability* (17.5%), and *Gram-Positive Definition* (11.3%).
*   ***Escherichia coli*** exhibits a highly balanced, multifaceted profile, with its justifications distributed across **9 distinct themes** (Themes 4 to 12). No single theme represents more than 22% of E. coli claims, proving E. coli is uniquely suited as a general-purpose biological reference, technical cell factory, and pathogenesis model.
