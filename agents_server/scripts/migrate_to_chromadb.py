import chromadb
import faiss
import pickle
import pandas as pd
import numpy as np
import os
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

def load_faiss_data(base_dir: str = None):
    """Load FAISS index and metadata"""
    if base_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.join(script_dir, "..", "datasets")
    
    index_path = os.path.join(base_dir, "clinical_trials.faiss")
    metadata_path = os.path.join(base_dir, "clinical_trials_metadata.pkl")
    
    print(f"Loading FAISS index from: {index_path}")
    print(f"Loading metadata from: {metadata_path}")
    
    try:
        # Load FAISS index
        index = faiss.read_index(index_path)
        print(f"Loaded FAISS index with {index.ntotal} vectors")
        
        # Load metadata
        with open(metadata_path, "rb") as f:
            metadata = pickle.load(f)
        
        documents = metadata["documents"]
        df = metadata["df"]
        
        print(f"Loaded {len(documents)} documents and DataFrame with {len(df)} rows")
        
        return index, documents, df
    
    except FileNotFoundError as e:
        print(f"Error: Could not find required files: {e}")
        return None, None, None
    except Exception as e:
        print(f"Error loading data: {e}")
        return None, None, None

def extract_embeddings_from_faiss(index: faiss.Index) -> np.ndarray:
    """Extract embeddings from FAISS index"""
    try:
        # For IndexFlatIP, we can reconstruct the vectors
        embeddings = np.zeros((index.ntotal, index.d), dtype=np.float32)
        index.reconstruct_n(0, index.ntotal, embeddings)
        return embeddings
    except Exception as e:
        print(f"Error extracting embeddings: {e}")
        return None

def migrate_to_chromadb(
    client: chromadb.CloudClient,
    collection_name: str = "ClinicalAgents",
    batch_size: int = 100
):
    """Migrate FAISS data to ChromaDB"""
    
    # Load FAISS data
    index, documents, df = load_faiss_data()
    if index is None:
        return False
    
    # Extract embeddings
    print("Extracting embeddings from FAISS index...")
    embeddings = extract_embeddings_from_faiss(index)
    if embeddings is None:
        return False
    
    print(f"Extracted embeddings shape: {embeddings.shape}")
    
    try:
        # Create or get collection
        try:
            collection = client.get_collection(collection_name)
            print(f"Found existing collection '{collection_name}'. Deleting and recreating...")
            client.delete_collection(collection_name)
        except Exception:
            print(f"Collection '{collection_name}' doesn't exist. Creating new one...")
        
        collection = client.create_collection(collection_name)
        print(f"Created collection '{collection_name}'")
        
        # Prepare data for ChromaDB
        total_docs = len(documents)
        print(f"Preparing to add {total_docs} documents to ChromaDB...")
        
        # Process in batches
        for i in range(0, total_docs, batch_size):
            end_idx = min(i + batch_size, total_docs)
            batch_size_actual = end_idx - i
            
            print(f"Processing batch {i//batch_size + 1}: documents {i+1}-{end_idx}")
            
            # Prepare batch data
            batch_ids = [str(i + j) for j in range(batch_size_actual)]
            batch_documents = documents[i:end_idx]
            batch_embeddings = embeddings[i:end_idx].tolist()
            
            # Prepare metadata for each document
            batch_metadata = []
            for j in range(batch_size_actual):
                row_data = df.iloc[i + j]
                metadata = {
                    "nct_id": str(row_data.get("NCT ID", "N/A")),
                    "disease": str(row_data.get("Disease", "N/A")),
                    "status": str(row_data.get("Overall Status", "N/A")),
                    "phase": str(row_data.get("Phase", "N/A")),
                    "conditions": str(row_data.get("Conditions", "N/A")),
                    "study_type": str(row_data.get("Study type", "N/A")),
                    "why_stopped": str(row_data.get("Why Stopped", "N/A")),
                    "eligibility_criteria": str(row_data.get("Eligibility Criteria", "N/A"))[:1000],  # Truncate long text
                    "original_index": i + j
                }
                batch_metadata.append(metadata)
            
            # Add batch to collection
            collection.add(
                ids=batch_ids,
                documents=batch_documents,
                embeddings=batch_embeddings,
                metadatas=batch_metadata
            )
            
            print(f"Added batch {i//batch_size + 1}/{(total_docs + batch_size - 1)//batch_size}")
        
        print(f"\nSuccessfully migrated {total_docs} documents to ChromaDB collection '{collection_name}'")
        
        # Verify the migration
        count = collection.count()
        print(f"Collection now contains {count} documents")
        
        return True
        
    except Exception as e:
        print(f"Error migrating to ChromaDB: {e}")
        return False

def test_chromadb_search(
    client: chromadb.CloudClient,
    collection_name: str = "clinical_trials",
    query: str = "breast cancer phase 3 trial eligibility",
    n_results: int = 3
):
    """Test search functionality in ChromaDB"""
    try:
        collection = client.get_collection(collection_name)
        
        # Load sentence transformer for query encoding
        model = SentenceTransformer("all-MiniLM-L6-v2")
        query_embedding = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        
        # Search
        results = collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results
        )
        
        print(f"\n{'='*60}")
        print(f"Search Results for: '{query}'")
        print(f"{'='*60}")
        
        for i in range(len(results['ids'][0])):
            print(f"\n--- Result {i+1} ---")
            print(f"ID: {results['ids'][0][i]}")
            print(f"Distance: {results['distances'][0][i]:.4f}")
            print(f"NCT ID: {results['metadatas'][0][i].get('nct_id', 'N/A')}")
            print(f"Disease: {results['metadatas'][0][i].get('disease', 'N/A')}")
            print(f"Phase: {results['metadatas'][0][i].get('phase', 'N/A')}")
            print(f"Status: {results['metadatas'][0][i].get('status', 'N/A')}")
            print(f"Document: {results['documents'][0][i][:200]}...")
        
        return True
        
    except Exception as e:
        print(f"Error testing search: {e}")
        return False

def main():
    """Main migration function"""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Validate required environment variables
    api_key = os.getenv('CHROMA_API_KEY')
    tenant = os.getenv('CHROMA_TENANT')
    database = os.getenv('CHROMA_DATABASE', 'ClinicalAgents')
    
    if not api_key:
        raise ValueError("CHROMA_API_KEY environment variable is required")
    if not tenant:
        raise ValueError("CHROMA_TENANT environment variable is required")
    
    # Initialize ChromaDB client
    client = chromadb.CloudClient(
        api_key=api_key,
        tenant=tenant,
        database=database
    )
    
    print("Connected to ChromaDB Cloud")
    
    # List existing collections
    try:
        collections = client.list_collections()
        print(f"Existing collections: {[col.name for col in collections]}")
    except Exception as e:
        print(f"Error listing collections: {e}")
    
    # Migrate data
    success = migrate_to_chromadb(client, collection_name="clinical_trials")
    
    if success:
        print("\nMigration completed successfully!")
        
        # Test the search functionality
        print("\nTesting search functionality...")
        test_chromadb_search(client, collection_name="clinical_trials")
    else:
        print("Migration failed!")

if __name__ == "__main__":
    main()