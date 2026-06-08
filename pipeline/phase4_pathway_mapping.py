import pandas as pd
import os

def main():
    # Define the 13 clusters mapping details
    mapping_data = [
        {
            "cluster_id": 0,
            "cluster_name": "Gram-Positive Physiology, Endospore Formation, and Industrial Bioprocessing (B. subtilis)",
            "dominant_organism": "B. subtilis",
            "biological_system": "Endospore formation, quorum sensing, and Gram-positive cell physiology",
            "kegg_pathway_id": "bsu02020, bsu02024, bsu03070",
            "kegg_pathway_name": "Two-component system, Quorum sensing, Bacterial secretion system",
            "ecocyc_pathway": "N/A"
        },
        {
            "cluster_id": 1,
            "cluster_name": "Gram-Positive Bacterium Model Definition",
            "dominant_organism": "B. subtilis",
            "biological_system": "Gram-positive cell wall biogenesis and peptidoglycan assembly",
            "kegg_pathway_id": "bsu00550",
            "kegg_pathway_name": "Peptidoglycan biosynthesis",
            "ecocyc_pathway": "N/A"
        },
        {
            "cluster_id": 2,
            "cluster_name": "Eukaryotic Cell Biology, Conserved Metabolic Pathways, and Human Disease Modeling (S. cerevisiae)",
            "dominant_organism": "S. cerevisiae",
            "biological_system": "Conserved eukaryotic cell biology, endoplasmic reticulum processing, longevity pathways, and disease homologues",
            "kegg_pathway_id": "sce04111, sce04113, sce04213, sce04141",
            "kegg_pathway_name": "Cell cycle - yeast, Meiosis - yeast, Longevity regulating pathway - yeast, Protein processing in endoplasmic reticulum",
            "ecocyc_pathway": "N/A"
        },
        {
            "cluster_id": 3,
            "cluster_name": "Genetic Tractability, Molecular Tooling, and Industrial Cell Factories",
            "dominant_organism": "S. cerevisiae",
            "biological_system": "Homologous recombination, genetic transformation, and secondary metabolite biosynthesis",
            "kegg_pathway_id": "sce03440, eco03440, bsu03440",
            "kegg_pathway_name": "Homologous recombination",
            "ecocyc_pathway": "double-strand break repair, homologous recombination"
        },
        {
            "cluster_id": 4,
            "cluster_name": "Experimental Rationale for Organism Selection (E. coli)",
            "dominant_organism": "E. coli",
            "biological_system": "Rapid cell culture, sulfur assimilation, and chaperone-mediated stress response",
            "kegg_pathway_id": "eco00920, eco03018",
            "kegg_pathway_name": "Sulfur metabolism, RNA degradation",
            "ecocyc_pathway": "heat shock response regulation, transcription initiation"
        },
        {
            "cluster_id": 5,
            "cluster_name": "Standard Model Bacterium Utility and Characterization (E. coli)",
            "dominant_organism": "E. coli",
            "biological_system": "Core metabolic modeling and standard cellular physiology",
            "kegg_pathway_id": "eco01100",
            "kegg_pathway_name": "Metabolic pathways",
            "ecocyc_pathway": "E. coli K-12 core metabolic reconstruction"
        },
        {
            "cluster_id": 6,
            "cluster_name": "Heterologous Protein Expression and Recombinant Production Chassis (E. coli)",
            "dominant_organism": "E. coli",
            "biological_system": "Recombinant protein translation, Sec/Tat secretion translocation, and ribosome function",
            "kegg_pathway_id": "eco03010, eco03060, eco03070",
            "kegg_pathway_name": "Ribosome, Protein export, Bacterial secretion system",
            "ecocyc_pathway": "Sec-dependent protein translocation, Tat-dependent protein translocation"
        },
        {
            "cluster_id": 7,
            "cluster_name": "Clinical Pathogenesis, Virulence Modeling, and Infectious Disease (E. coli)",
            "dominant_organism": "E. coli",
            "biological_system": "Virulence determinants (fimbriae/pili), lipopolysaccharide assembly, and host cell infection pathways",
            "kegg_pathway_id": "map05130, eco00540",
            "kegg_pathway_name": "Pathogenic Escherichia coli infection, Lipopolysaccharide biosynthesis",
            "ecocyc_pathway": "O-antigen biosynthesis, Lipid A biosynthesis, pili assembly"
        },
        {
            "cluster_id": 8,
            "cluster_name": "Gram-Negative Reference Organism and Cell Envelope Modeling (E. coli)",
            "dominant_organism": "E. coli",
            "biological_system": "Gram-negative envelope assembly, outer membrane biogenesis, and peptidoglycan cross-linking",
            "kegg_pathway_id": "eco00550, eco00540",
            "kegg_pathway_name": "Peptidoglycan biosynthesis, Lipopolysaccharide biosynthesis",
            "ecocyc_pathway": "murein peptidoglycan biosynthesis, outer membrane assembly"
        },
        {
            "cluster_id": 9,
            "cluster_name": "Antimicrobial Screening, Drug Tolerance, and Resistance Mechanisms (E. coli)",
            "dominant_organism": "E. coli",
            "biological_system": "Beta-lactam resistance, cationic peptide barriers, and multidrug efflux transport",
            "kegg_pathway_id": "eco01501, eco01503, eco02010",
            "kegg_pathway_name": "beta-Lactam resistance, Cationic antimicrobial peptide (CAMP) resistance, ABC transporters",
            "ecocyc_pathway": "AcrAB-TolC multidrug efflux, antibiotic resistance genes"
        },
        {
            "cluster_id": 10,
            "cluster_name": "DNA Replication, Recombination, Repair, and Replication Fidelity (E. coli)",
            "dominant_organism": "E. coli",
            "biological_system": "DNA replication fork, mismatch repair, nucleotide excision repair, and homologous recombination",
            "kegg_pathway_id": "eco03030, eco03430, eco03420, eco03440",
            "kegg_pathway_name": "DNA replication, Mismatch repair, Nucleotide excision repair, Homologous recombination",
            "ecocyc_pathway": "chromosomal DNA replication, methyl-directed mismatch repair, double-strand break repair"
        },
        {
            "cluster_id": 11,
            "cluster_name": "Bacterial Reference Standard and Legacy Model Characterization (E. coli)",
            "dominant_organism": "E. coli",
            "biological_system": "Reference proteome annotations and baseline K-12 metabolic network",
            "kegg_pathway_id": "eco01100",
            "kegg_pathway_name": "Metabolic pathways",
            "ecocyc_pathway": "MG1655 reference database"
        },
        {
            "cluster_id": 12,
            "cluster_name": "Genomic Annotation and Molecular Genetics Reference (E. coli)",
            "dominant_organism": "E. coli",
            "biological_system": "Transcription regulation, small RNA networks, and sensory signal transduction",
            "kegg_pathway_id": "eco03020, eco02020",
            "kegg_pathway_name": "RNA polymerase, Two-component system",
            "ecocyc_pathway": "transcription factor networks, small RNA regulatory networks"
        }
    ]
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(mapping_data)
    os.makedirs("data/processed", exist_ok=True)
    df.to_csv("data/processed/phase4_pathway_map.csv", index=False)
    print("Successfully created biological pathway mapping file data/processed/phase4_pathway_map.csv!")

if __name__ == "__main__":
    main()
