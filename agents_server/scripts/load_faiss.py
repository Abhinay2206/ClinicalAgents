import pandas as pd
import faiss
import numpy as np
import pickle
import os
from sentence_transformers import SentenceTransformer

# Get the correct path to the CSV file
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, "..", "datasets", "clinical_trials.csv")

try:
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows from {csv_path}")
except FileNotFoundError:
    print(f"Error: Could not find {csv_path}")
    exit(1)
except Exception as e:
    print(f"Error loading CSV: {e}")
    exit(1)

def row_to_text(row):
    def safe_get(field, default="N/A"):
        value = row.get(field, default)
        return str(value) if pd.notna(value) else default
    
    return (
        f"Disease: {safe_get('Disease')}. "
        f"NCT ID: {safe_get('NCT ID')}. "
        f"Status: {safe_get('Overall Status')}. "
        f"Why Stopped: {safe_get('Why Stopped')}. "
        f"Eligibility: {safe_get('Eligibility Criteria')}. "
        f"Phase: {safe_get('Phase')}. "
        f"Conditions: {safe_get('Conditions')}. "
        f"Study Type: {safe_get('Study type')}."
    )

documents = df.apply(row_to_text, axis=1).tolist()

model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(documents, convert_to_numpy=True, normalize_embeddings=True)

d = embeddings.shape[1]  # dimension of embeddings
index = faiss.IndexFlatIP(d)  # Inner Product (cosine similarity)
index.add(embeddings)

print("FAISS index created with", index.ntotal, "vectors")

index_path = os.path.join(script_dir, "clinical_trials.faiss")
metadata_path = os.path.join(script_dir, "clinical_trials_metadata.pkl")

faiss.write_index(index, index_path)

with open(metadata_path, "wb") as f:
    pickle.dump({"documents": documents, "df": df}, f)

print(f"Saved {index_path} and {metadata_path}")

def search(query, top_k=5):
    # Get file paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(script_dir, "clinical_trials.faiss")
    metadata_path = os.path.join(script_dir, "clinical_trials_metadata.pkl")
    
    try:
        # Load index
        index = faiss.read_index(index_path)
        
        # Load metadata
        with open(metadata_path, "rb") as f:
            metadata = pickle.load(f)
        documents = metadata["documents"]
        df = metadata["df"]

        # Load model for encoding query
        model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Encode query
        q_embedding = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        
        # Search
        D, I = index.search(q_embedding, k=top_k)
        
        results = []
        for idx in I[0]:
            results.append({
                "text": documents[idx],
                "row": df.iloc[idx].to_dict(),
                "score": float(D[0][len(results)])  # Add similarity score
            })
        return results
    
    except FileNotFoundError as e:
        print(f"Error: Could not find required files. Make sure to run the indexing first. {e}")
        return []
    except Exception as e:
        print(f"Error during search: {e}")
        return []

if __name__ == "__main__":
    # Test the search functionality
    print("\n" + "="*50)
    print("Testing search functionality...")
    print("="*50)
    
    query = "breast cancer phase 3 trial eligibility"
    results = search(query, top_k=3)
    
    if results:
        print(f"\nFound {len(results)} results for query: '{query}'")
        for i, r in enumerate(results, 1):
            print(f"\n--- Result {i} (Score: {r.get('score', 'N/A'):.4f}) ---")
            print(r["text"])
            print(f"NCT ID: {r['row'].get('NCT ID', 'N/A')}")
    else:
        print("No results found or search failed.")
