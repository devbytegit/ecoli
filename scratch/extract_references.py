import pandas as pd
import os
import sys

# Define paths
base_dir = r"C:\Users\olufi\Desktop\QUICK FILES\ECOLI"
clustered_claims_path = os.path.join(base_dir, "data", "processed", "phase3_clustered_claims.csv")
corpus_raw_path = os.path.join(base_dir, "data", "raw", "corpus_raw.csv")
cluster_summary_path = os.path.join(base_dir, "data", "processed", "phase3_cluster_summary.csv")
output_path = os.path.join(base_dir, "scratch", "extracted_references.txt")

# Load data
df_claims = pd.read_csv(clustered_claims_path)
df_raw = pd.read_csv(corpus_raw_path)
df_summary = pd.read_csv(cluster_summary_path)

df_claims['paper_id'] = df_claims['paper_id'].astype(str)
df_raw['paper_id'] = df_raw['paper_id'].astype(str)

out_lines = []
out_lines.append("--- HISTORICAL REFERENCES ---")
hist_refs = [
    {
        "id": "Escherich1885",
        "citation": "Escherich, T. (1885). Die Darmbacterien des Säuglings und ihre Beziehungen zur Physiologie der Verdauung. *Fortschritte der Medizin*, 3, 515–522."
    },
    {
        "id": "Lederberg1946",
        "citation": "Lederberg, J., & Tatum, E. L. (1946). Gene recombination in *Escherichia coli*. *Nature*, 158(4016), 558."
    },
    {
        "id": "Blattner1997",
        "citation": "Blattner, F. R., Plunkett, G., Bloch, C. A., Perna, N. T., Burland, V., Riley, M., ... & Guyer, M. S. (1997). The complete genome sequence of *Escherichia coli* K-12. *Science*, 277(5331), 1453-1462. PMID: 9278503"
    },
    {
        "id": "Kuhn1962",
        "citation": "Kuhn, T. S. (1962). *The Structure of Scientific Revolutions*. University of Chicago Press."
    }
]

for ref in hist_refs:
    out_lines.append(f"[{ref['id']}]: {ref['citation']}")

out_lines.append("\n--- CLUSTER EXEMPLARS ---")
for idx, row in df_summary.iterrows():
    cluster_id = row['cluster_id']
    if cluster_id == -1:
        continue
    
    theme_name = row['theme_name']
    claims_list = str(row['representative_claims_top10']).split(' | ')
    first_claim = claims_list[0].strip()
    
    # Let's find matches in df_claims for this cluster
    matches = df_claims[(df_claims['cluster_id'] == cluster_id) & (df_claims['claim'].str.contains(first_claim[:40], case=False, na=False))]
    
    if matches.empty:
        matches = df_claims[df_claims['cluster_id'] == cluster_id].sort_values(by='cluster_probability', ascending=False)
        
    if not matches.empty:
        best_match = matches.iloc[0]
        pid = best_match['paper_id']
        claim_text = best_match['claim']
        
        # Get details from df_raw
        raw_match = df_raw[df_raw['paper_id'] == pid]
        if not raw_match.empty:
            paper = raw_match.iloc[0]
            authors = paper['authors']
            if pd.isna(authors) or authors == '':
                authors = "Unknown Authors"
            
            auth_split = str(authors).split(',')
            if len(auth_split) > 3:
                author_str = f"{auth_split[0].strip()} et al."
            else:
                author_str = str(authors).strip()
                
            title = paper['title']
            journal = paper['journal']
            year = paper['year']
            
            # normalize non-breaking hyphen and other punctuation
            title = title.replace('\u2011', '-').replace('\u2013', '-').replace('\u2014', '-')
            author_str = author_str.replace('\u2011', '-').replace('\u2013', '-').replace('\u2014', '-')
            
            ref_str = f"{author_str} ({year}). {title}. *{journal}*. PMID: {pid}"
            out_lines.append(f"[Cluster {cluster_id} - PMID {pid}]: {ref_str} (Claim: '{claim_text}')")
        else:
            out_lines.append(f"[Cluster {cluster_id} - PMID {pid}]: Raw paper details not found (Claim: '{claim_text}')")
    else:
        out_lines.append(f"[Cluster {cluster_id}]: No claim match found")

with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines))

print(f"Success! Output written to {output_path}")
