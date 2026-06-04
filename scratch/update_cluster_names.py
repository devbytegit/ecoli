import pandas as pd

def main():
    summary_path = "data/processed/phase3_cluster_summary.csv"
    df = pd.read_csv(summary_path)
    
    cluster_names = {
        0: "Gram-Positive Physiology, Endospore Formation, and Industrial Bioprocessing (B. subtilis)",
        1: "Gram-Positive Bacterium Model Definition",
        2: "Eukaryotic Cell Biology, Conserved Metabolic Pathways, and Human Disease Modeling (S. cerevisiae)",
        3: "Genetic Tractability, Molecular Tooling, and Industrial Cell Factories",
        4: "Experimental Rationale for Organism Selection (E. coli)",
        5: "Standard Model Bacterium Utility and Characterization (E. coli)",
        6: "Heterologous Protein Expression and Recombinant Production Chassis (E. coli)",
        7: "Clinical Pathogenesis, Virulence Modeling, and Infectious Disease (E. coli)",
        8: "Gram-Negative Reference Organism and Cell Envelope Modeling (E. coli)",
        9: "Antimicrobial Screening, Drug Tolerance, and Resistance Mechanisms (E. coli)",
        10: "DNA Replication, Recombination, Repair, and Replication Fidelity (E. coli)",
        11: "Bacterial Reference Standard and Legacy Model Characterization (E. coli)",
        12: "Genomic Annotation and Molecular Genetics Reference (E. coli)"
    }
    
    # Map the descriptive names to theme_name for valid clusters
    df.loc[df["cluster_id"].isin(cluster_names.keys()), "theme_name"] = df["cluster_id"].map(cluster_names)
    
    df.to_csv(summary_path, index=False)
    print("Successfully updated cluster names in phase3_cluster_summary.csv!")

if __name__ == "__main__":
    main()
