import os
import sys
import numpy as np
import pandas as pd
import torch
import matplotlib.pyplot as plt
import seaborn as sns
from sentence_transformers import SentenceTransformer
import umap
from sklearn.cluster import HDBSCAN

def main():
    # Configure output to support UTF-8 characters on Windows consoles
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

    print("="*60)
    print("PHASE 3: SEMANTIC EMBEDDING + HDBSCAN CLUSTERING PIPELINE")
    print("="*60)
    
    # 1. Setup paths
    input_path = "data/processed/phase3_input.csv"
    embeddings_out_path = "data/processed/phase3_embeddings.npy"
    clustered_claims_out_path = "data/processed/phase3_clustered_claims.csv"
    summary_out_path = "data/processed/phase3_cluster_summary.csv"
    umap_plot_path = "data/figures/phase3_umap_clusters.png"
    dist_plot_path = "data/figures/phase3_cluster_distribution.png"
    
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("data/figures", exist_ok=True)
    
    # 2. Load input data
    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' not found!")
        sys.exit(1)
        
    print(f"Loading input claims from '{input_path}'...")
    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} rows.")
    
    # Clean claims
    df['claim'] = df['claim'].astype(str).str.strip()
    df = df[df['claim'] != ""].reset_index(drop=True)
    print(f"After cleaning empty claims: {len(df)} rows ready for clustering.")
    
    # 3. Generate or Load PubMedBERT Embeddings
    if os.path.exists(embeddings_out_path):
        print(f"Found cached embeddings at '{embeddings_out_path}'. Loading...")
        embeddings = np.load(embeddings_out_path)
        print(f"Embeddings loaded successfully. Shape: {embeddings.shape}")
    else:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {device.upper()}")
        
        model_name = "pritamdeka/S-PubMedBert-MS-MARCO"
        print(f"Loading embedding model '{model_name}'...")
        model = SentenceTransformer(model_name, device=device)
        
        print("Generating embeddings (this may take a moment)...")
        claims = df['claim'].tolist()
        embeddings = model.encode(claims, show_progress_bar=True, batch_size=32)
        
        print(f"Saving embeddings to '{embeddings_out_path}'...")
        np.save(embeddings_out_path, embeddings)
        print(f"Embeddings saved successfully. Shape: {embeddings.shape}")
    
    # 4. Dimensionality Reduction (10D UMAP for Clustering)
    print("Reducing dimensionality to 10D using UMAP (cosine metric) for clustering...")
    reducer_10d = umap.UMAP(
        n_neighbors=15,
        n_components=10,
        metric='cosine',
        random_state=42
    )
    embeddings_10d = reducer_10d.fit_transform(embeddings)
    print("10D reduction complete.")
    
    # 5. HDBSCAN Clustering with Parameter Optimization Search
    print("Optimizing HDBSCAN parameters (searching for 8-18 clusters with < 30% noise)...")
    
    best_params = None
    best_score = -1.0
    best_labels = None
    best_probabilities = None
    best_num_clusters = 0
    best_noise_pct = 100.0
    
    # Define grid search space
    min_cluster_sizes = [10, 12, 15, 18, 20, 25, 30]
    min_samples_opts = [3, 5, 8, 10, 12, 15]
    
    search_results = []
    
    for mcs in min_cluster_sizes:
        for ms in min_samples_opts:
            if ms > mcs:
                continue
            
            clusterer = HDBSCAN(
                min_cluster_size=mcs,
                min_samples=ms,
                metric='euclidean'
            )
            clusterer.fit(embeddings_10d)
            
            lbls = clusterer.labels_
            probs = clusterer.probabilities_
            
            num_c = len(set(lbls)) - (1 if -1 in lbls else 0)
            noise_c = np.sum(lbls == -1)
            noise_p = (noise_c / len(df)) * 100
            
            # Calculate silhouette score for clustered points (excluding noise)
            clust_mask = (lbls != -1)
            if np.sum(clust_mask) > 0 and len(set(lbls[clust_mask])) > 1:
                from sklearn.metrics import silhouette_score
                sil = silhouette_score(embeddings_10d[clust_mask], lbls[clust_mask])
            else:
                sil = -1.0
                
            search_results.append({
                'min_cluster_size': mcs,
                'min_samples': ms,
                'num_clusters': num_c,
                'noise_pct': noise_p,
                'silhouette': sil
            })
            
            # Prof. Claude's target criteria: 8-18 clusters, noise < 30%
            is_valid = (8 <= num_c <= 18) and (noise_p < 30.0)
            
            if is_valid:
                # Prioritize higher silhouette score
                if sil > best_score:
                    best_score = sil
                    best_params = (mcs, ms)
                    best_labels = lbls
                    best_probabilities = probs
                    best_num_clusters = num_c
                    best_noise_pct = noise_p
                    
    # If no combination meets the strict 8-18 range, relax criteria
    if best_params is None:
        print("Warning: No parameter set yielded between 8-18 clusters with < 30% noise.")
        print("Selecting best alternative based on relaxed cluster count (5-25) and low noise (< 35%)...")
        
        for res in search_results:
            mcs, ms = res['min_cluster_size'], res['min_samples']
            num_c, noise_p, sil = res['num_clusters'], res['noise_pct'], res['silhouette']
            
            if (5 <= num_c <= 25) and (noise_p < 35.0):
                if sil > best_score:
                    best_score = sil
                    best_params = (mcs, ms)
                    best_num_clusters = num_c
                    best_noise_pct = noise_p
                    
    # If still None, default to a fallback
    if best_params is None:
        print("Using default fallback parameters (min_cluster_size=15, min_samples=5)")
        best_params = (15, 5)
        
    # Run best clustering
    mcs, ms = best_params
    print(f"Selected Parameters: min_cluster_size={mcs}, min_samples={ms}")
    
    clusterer = HDBSCAN(
        min_cluster_size=mcs,
        min_samples=ms,
        metric='euclidean'
    )
    clusterer.fit(embeddings_10d)
    labels = clusterer.labels_
    probabilities = clusterer.probabilities_
    
    df['cluster_id'] = labels
    df['cluster_probability'] = probabilities
    
    num_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    noise_count = np.sum(labels == -1)
    noise_pct = (noise_count / len(df)) * 100
    
    print(f"Final Clustering complete. Found {num_clusters} clusters.")
    print(f"Noise points (outliers marked -1): {noise_count} ({noise_pct:.2f}%)")
    
    # Calculate Silhouette Score (excluding noise points)
    clustered_mask = (labels != -1)
    if np.sum(clustered_mask) > 0 and len(set(labels[clustered_mask])) > 1:
        from sklearn.metrics import silhouette_score
        sil_score = silhouette_score(embeddings_10d[clustered_mask], labels[clustered_mask])
        print(f"Silhouette Score (excluding noise): {sil_score:.4f}")
    else:
        sil_score = -1.0
        print("Silhouette Score (excluding noise): N/A")
    
    # 6. Dimensionality Reduction (2D UMAP for Visualization)
    print("Reducing dimensionality to 2D using UMAP (cosine metric) for plotting...")
    reducer_2d = umap.UMAP(
        n_neighbors=15,
        n_components=2,
        metric='cosine',
        random_state=42
    )
    embeddings_2d = reducer_2d.fit_transform(embeddings)
    df['umap_x'] = embeddings_2d[:, 0]
    df['umap_y'] = embeddings_2d[:, 1]
    print("2D reduction complete.")
    
    # 7. Generate Cluster Visualizations
    print("Generating UMAP cluster plot...")
    plt.figure(figsize=(12, 10), dpi=300)
    
    # Set premium aesthetic style
    sns.set_theme(style="whitegrid")
    
    # Separate noise and clustered points
    noise_mask = (labels == -1)
    
    # Generate a sleek color palette for the clusters
    unique_labels = sorted(list(set(labels)))
    cluster_labels = [l for l in unique_labels if l != -1]
    
    # Use husl or a harmonious color cycle
    colors = sns.color_palette("husl", len(cluster_labels))
    color_map = {l: colors[i] for i, l in enumerate(cluster_labels)}
    color_map[-1] = (0.85, 0.85, 0.85)  # Light gray for noise
    
    # Plot noise points first (in background)
    plt.scatter(
        df.loc[noise_mask, 'umap_x'],
        df.loc[noise_mask, 'umap_y'],
        c=[color_map[-1]],
        label='Noise/Outliers',
        alpha=0.3,
        s=15,
        edgecolors='none'
    )
    
    # Plot clustered points
    for cid in cluster_labels:
        cid_mask = (labels == cid)
        plt.scatter(
            df.loc[cid_mask, 'umap_x'],
            df.loc[cid_mask, 'umap_y'],
            c=[color_map[cid]],
            label=f'Cluster {cid}',
            alpha=0.8,
            s=25,
            edgecolors='w',
            linewidths=0.2
        )
        
        # Optionally annotate cluster centroids in 2D space for clarity
        centroid_2d = embeddings_2d[cid_mask].mean(axis=0)
        plt.annotate(
            str(cid),
            xy=(centroid_2d[0], centroid_2d[1]),
            xytext=(0, 0),
            textcoords='offset points',
            fontsize=12,
            weight='bold',
            color='black',
            bbox=dict(boxstyle="round,pad=0.2", fc="yellow", alpha=0.6, ec="black", lw=0.5)
        )
        
    plt.title("UMAP 2D Projection of Thematic Justification Clusters", fontsize=16, pad=15, weight='bold')
    plt.xlabel("UMAP Dimension 1", fontsize=12)
    plt.ylabel("UMAP Dimension 2", fontsize=12)
    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0, title="Themes", title_fontsize=12)
    plt.tight_layout()
    plt.savefig(umap_plot_path, bbox_inches='tight')
    plt.close()
    print(f"UMAP plot saved to '{umap_plot_path}'")
    
    # 8. Save Clustered Claims Table
    print(f"Saving clustered claims to '{clustered_claims_out_path}'...")
    df.to_csv(clustered_claims_out_path, index=False)
    
    # 9. Build Cluster Summary & Exemplar Extraction
    print("Building cluster summaries and extracting exemplars...")
    summary_data = []
    
    for cid in unique_labels:
        if cid == -1:
            name = "Outliers/Noise"
        else:
            name = f"Cluster {cid}"
            
        cluster_df = df[df['cluster_id'] == cid]
        size = len(cluster_df)
        pct = (size / len(df)) * 100
        
        # Organism Distribution
        org_counts = cluster_df['organism'].value_counts()
        dominant_org = org_counts.index[0] if len(org_counts) > 0 else "N/A"
        org_breakdown_str = ", ".join([f"{org}: {count} ({count/size*100:.1f}%)" for org, count in org_counts.items()])
        
        # Organism percentages
        ecoli_pct = round((org_counts.get('E. coli', 0) / size) * 100, 2)
        cerevisiae_pct = round((org_counts.get('S. cerevisiae', 0) / size) * 100, 2)
        subtilis_pct = round((org_counts.get('B. subtilis', 0) / size) * 100, 2)
        
        # LLM Category Distribution
        cat_counts = cluster_df['category'].value_counts()
        dominant_cat = cat_counts.index[0] if len(cat_counts) > 0 else "N/A"
        cat_breakdown_str = ", ".join([f"{cat}: {count} ({count/size*100:.1f}%)" for cat, count in cat_counts.items()])
        
        # Category percentages
        historical_pct = round((cat_counts.get('historical', 0) / size) * 100, 2)
        biological_pct = round((cat_counts.get('biological', 0) / size) * 100, 2)
        technical_pct = round((cat_counts.get('technical', 0) / size) * 100, 2)
        economic_pct = round((cat_counts.get('economic', 0) / size) * 100, 2)
        cultural_pct = round((cat_counts.get('cultural', 0) / size) * 100, 2)
        
        # Representative Claims (Exemplars)
        # We calculate the distance of each cluster member to the cluster's 10D centroid
        if cid == -1:
            # For noise, just grab top elements by probability (usually 0) or simply first 10
            rep_claims = cluster_df.head(10)['claim'].tolist()
        else:
            cluster_embeddings_10d = embeddings_10d[df['cluster_id'] == cid]
            centroid_10d = cluster_embeddings_10d.mean(axis=0)
            distances = np.linalg.norm(cluster_embeddings_10d - centroid_10d, axis=1)
            
            # Sort by distance
            sorted_indices = np.argsort(distances)
            rep_claims = cluster_df.iloc[sorted_indices].head(10)['claim'].tolist()
            
        rep_claims_str = " | ".join(rep_claims)
        
        summary_data.append({
            'cluster_id': cid,
            'theme_name': name,
            'size': size,
            'percentage': round(pct, 2),
            'dominant_organism': dominant_org,
            'ecoli_pct': ecoli_pct,
            's_cerevisiae_pct': cerevisiae_pct,
            'b_subtilis_pct': subtilis_pct,
            'organism_distribution': org_breakdown_str,
            'dominant_category': dominant_cat,
            'historical_pct': historical_pct,
            'biological_pct': biological_pct,
            'technical_pct': technical_pct,
            'economic_pct': economic_pct,
            'cultural_pct': cultural_pct,
            'category_distribution': cat_breakdown_str,
            'representative_claims_top10': rep_claims_str
        })
        
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(summary_out_path, index=False)
    print(f"Summary table saved to '{summary_out_path}'")
    
    # 10. Generate Organism Stacked Distribution Bar Chart
    print("Generating stacked distribution plot across organisms...")
    # Group by cluster (excluding noise) and organism to see relative sizes
    clustered_df = df[df['cluster_id'] != -1]
    if len(clustered_df) > 0:
        org_cluster_counts = clustered_df.groupby(['cluster_id', 'organism']).size().unstack(fill_value=0)
        # Normalize to get percentages within each cluster
        org_cluster_pcts = org_cluster_counts.div(org_cluster_counts.sum(axis=1), axis=0) * 100
        
        plt.figure(figsize=(12, 7), dpi=300)
        org_cluster_pcts.plot(kind='bar', stacked=True, color=['#1f77b4', '#ff7f0e', '#2ca02c'], ax=plt.gca())
        
        plt.title("Organism Distribution Across Thematic Justification Clusters", fontsize=14, weight='bold', pad=15)
        plt.xlabel("Cluster ID", fontsize=12)
        plt.ylabel("Percentage (%)", fontsize=12)
        plt.legend(title="Organism", bbox_to_anchor=(1.02, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(dist_plot_path, bbox_inches='tight')
        plt.close()
        print(f"Stacked distribution plot saved to '{dist_plot_path}'")
    else:
        print("Warning: No clusters found (excluding noise) to plot stacked distribution.")
        
    # 11. Print Summary Report
    print("\n" + "="*60)
    print("FINAL PIPELINE SUMMARY REPORT")
    print("="*60)
    print(f"Total Claims Analyzed: {len(df)}")
    print(f"Clusters Detected:     {num_clusters}")
    print(f"Noise Claims (Outliers): {noise_count} ({noise_pct:.2f}%)")
    if 'sil_score' in locals():
        print(f"Silhouette Score (excl. noise): {sil_score:.4f}")
    print("-" * 60)
    
    for idx, row in summary_df.iterrows():
        if row['cluster_id'] == -1:
            continue
        print(f"Cluster {row['cluster_id']}: size={row['size']} ({row['percentage']:.2f}%)")
        print(f"  Dominant Organism: {row['dominant_organism']} ({row['organism_distribution'].split('(')[1].split(')')[0]})")
        print(f"  Dominant Category: {row['dominant_category']}")
        print(f"  Example Claim:     \"{row['representative_claims_top10'].split(' | ')[0]}\"")
        print("-" * 60)
        
    print("\nPipeline execution completed successfully!")
    print("="*60)

if __name__ == "__main__":
    main()
