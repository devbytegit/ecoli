import urllib.request
import json
import re

def query_kegg_find(org, keyword):
    keyword_escaped = urllib.parse.quote(keyword)
    url = f"http://rest.kegg.jp/find/pathway/{org}/{keyword_escaped}"
    try:
        with urllib.request.urlopen(url) as response:
            lines = response.read().decode('utf-8').strip().split('\n')
            results = []
            for line in lines:
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        results.append((parts[0], parts[1]))
            return results
    except Exception as e:
        print(f"Error querying KEGG for {org} and '{keyword}': {e}")
        return []

def main():
    print("Querying KEGG API for pathways...")
    
    # E. coli search
    print("\n--- E. coli pathways ('eco') ---")
    queries_eco = ["replication", "repair", "recombination", "pathogenic", "resistance", "secretion", "ribosome", "translation"]
    for q in queries_eco:
        res = query_kegg_find("eco", q)
        print(f"Query '{q}':")
        for pathway_id, name in res[:5]:
            print(f"  {pathway_id} - {name}")
            
    # Yeast search
    print("\n--- Yeast pathways ('sce') ---")
    queries_sce = ["cell cycle", "meiosis", "longevity", "MAPK", "endoplasmic"]
    for q in queries_sce:
        res = query_kegg_find("sce", q)
        print(f"Query '{q}':")
        for pathway_id, name in res[:5]:
            print(f"  {pathway_id} - {name}")
            
    # Bacillus search
    print("\n--- Bacillus subtilis pathways ('bsu') ---")
    queries_bsu = ["sporulation", "two-component", "secretion", "peptidoglycan"]
    for q in queries_bsu:
        res = query_kegg_find("bsu", q)
        print(f"Query '{q}':")
        for pathway_id, name in res[:5]:
            print(f"  {pathway_id} - {name}")

if __name__ == "__main__":
    main()
