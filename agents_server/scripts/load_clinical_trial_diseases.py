import pandas as pd
import os
from neo4j import GraphDatabase
import logging
from typing import Dict, List, Set
import time
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClinicalTrialNeo4jLoader:
    """Load only diseases from clinical trials and their Hetionet relationships"""
    
    def __init__(self, uri: str, username: str, password: str):
        """Initialize connection to Neo4j"""
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.verify_connection()
    
    def verify_connection(self):
        """Verify connection to Neo4j database"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                if test_value == 1:
                    logger.info("Successfully connected to Neo4j")
                else:
                    raise Exception("Connection test failed")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self):
        """Close the database connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def clear_database(self):
        """Clear all nodes and relationships from the database"""
        logger.info("Clearing existing data from database...")
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("Database cleared")
    
    def create_constraints_and_indexes(self):
        """Create constraints and indexes for better performance"""
        logger.info("Creating constraints and indexes...")
        
        constraints_and_indexes = [
            "CREATE CONSTRAINT hetionet_node_id IF NOT EXISTS FOR (n:HetionetNode) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT disease_id IF NOT EXISTS FOR (n:Disease) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT compound_id IF NOT EXISTS FOR (n:Compound) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT gene_id IF NOT EXISTS FOR (n:Gene) REQUIRE n.id IS UNIQUE",
            "CREATE INDEX hetionet_node_kind IF NOT EXISTS FOR (n:HetionetNode) ON (n.kind)",
            "CREATE INDEX hetionet_node_name IF NOT EXISTS FOR (n:HetionetNode) ON (n.name)",
        ]
        
        with self.driver.session() as session:
            for constraint_or_index in constraints_and_indexes:
                try:
                    session.run(constraint_or_index)
                except Exception as e:
                    if "already exists" in str(e).lower() or "equivalent" in str(e).lower():
                        continue
                    else:
                        logger.warning(f"Could not create constraint/index: {e}")
        
        logger.info("Constraints and indexes created")
    
    def extract_diseases_from_clinical_trials(self, csv_path: str) -> Set[str]:
        """Extract unique diseases from clinical trials CSV"""
        logger.info(f"Reading clinical trials from {csv_path}")
        
        df = pd.read_csv(csv_path)
        logger.info(f"Found {len(df)} clinical trials")
        
        # Extract diseases from both Disease and Conditions columns
        diseases = set()
        
        if 'Disease' in df.columns:
            diseases.update(df['Disease'].dropna().unique())
        
        if 'Conditions' in df.columns:
            # Conditions might have multiple conditions separated by |
            for conditions in df['Conditions'].dropna():
                if isinstance(conditions, str):
                    for condition in conditions.split('|'):
                        diseases.add(condition.strip())
        
        logger.info(f"Extracted {len(diseases)} unique diseases/conditions")
        return diseases
    
    def match_diseases_in_hetionet(self, diseases: Set[str], nodes_file: str) -> List[Dict]:
        """Find matching diseases in Hetionet nodes file"""
        logger.info(f"Matching diseases against Hetionet nodes...")
        
        df_nodes = pd.read_csv(nodes_file, sep='\t')
        
        # Filter for Disease type nodes only
        disease_nodes = df_nodes[df_nodes['kind'] == 'Disease'].copy()
        
        matched_diseases = []
        matched_names = set()
        
        # Match by exact name or case-insensitive
        diseases_lower = {d.lower(): d for d in diseases}
        
        for _, row in disease_nodes.iterrows():
            node_name = row['name']
            node_name_lower = node_name.lower()
            
            # Check for exact match or partial match
            if node_name_lower in diseases_lower or any(d in node_name_lower for d in diseases_lower.keys()):
                matched_diseases.append({
                    'id': row['id'],
                    'name': row['name'],
                    'kind': row['kind']
                })
                matched_names.add(node_name)
        
        logger.info(f"Matched {len(matched_diseases)} diseases in Hetionet")
        logger.info(f"Sample matched diseases: {list(matched_names)[:10]}")
        
        return matched_diseases
    
    def get_related_nodes_and_edges(self, disease_ids: Set[str], nodes_file: str, edges_file: str) -> tuple:
        """Get all nodes and edges related to the diseases"""
        logger.info("Finding related nodes and edges...")
        
        # Read all edges
        df_edges = pd.read_csv(edges_file, sep='\t')
        
        # Find edges connected to diseases
        related_edges = df_edges[
            (df_edges['source'].isin(disease_ids)) | 
            (df_edges['target'].isin(disease_ids))
        ]
        
        logger.info(f"Found {len(related_edges)} edges related to diseases")
        
        # Get all node IDs involved in these edges
        related_node_ids = set(related_edges['source'].unique()) | set(related_edges['target'].unique())
        
        # Read nodes and filter
        df_nodes = pd.read_csv(nodes_file, sep='\t')
        related_nodes = df_nodes[df_nodes['id'].isin(related_node_ids)]
        
        logger.info(f"Found {len(related_nodes)} nodes related to diseases")
        
        # Log node type distribution
        node_types = related_nodes['kind'].value_counts()
        logger.info("Related node type distribution:")
        for node_type, count in node_types.head(10).items():
            logger.info(f"  {node_type}: {count}")
        
        return related_nodes, related_edges
    
    def load_nodes(self, nodes_df: pd.DataFrame, batch_size: int = 1000):
        """Load nodes into Neo4j"""
        logger.info(f"Loading {len(nodes_df)} nodes...")
        
        total_created = 0
        with self.driver.session() as session:
            for i in range(0, len(nodes_df), batch_size):
                batch = nodes_df.iloc[i:i+batch_size]
                nodes_data = []
                
                for _, row in batch.iterrows():
                    nodes_data.append({
                        'id': row['id'],
                        'name': row['name'],
                        'kind': row['kind']
                    })
                
                # Create nodes with escaped labels
                nodes_created = 0
                for node_data in nodes_data:
                    try:
                        label_name = node_data['kind'].replace(' ', '_')
                        cypher = f"""
                        CREATE (n:HetionetNode:`{label_name}` {{
                            id: $id,
                            name: $name,
                            kind: $kind
                        }})
                        """
                        session.run(cypher, **node_data)
                        nodes_created += 1
                    except Exception as e:
                        logger.warning(f"Could not create node {node_data['id']}: {e}")
                
                total_created += nodes_created
                if (i // batch_size) % 5 == 0:
                    logger.info(f"Created {total_created} nodes so far...")
        
        logger.info(f"Successfully loaded {total_created} nodes")
        return total_created
    
    def load_edges(self, edges_df: pd.DataFrame, batch_size: int = 2000):
        """Load edges into Neo4j"""
        logger.info(f"Loading {len(edges_df)} edges...")
        
        total_created = 0
        with self.driver.session() as session:
            for i in range(0, len(edges_df), batch_size):
                batch = edges_df.iloc[i:i+batch_size]
                
                edges_created = 0
                for _, row in batch.iterrows():
                    try:
                        cypher = """
                        MATCH (source:HetionetNode {id: $source})
                        MATCH (target:HetionetNode {id: $target})
                        CREATE (source)-[r:HETIONET_EDGE {metaedge: $metaedge}]->(target)
                        RETURN r
                        """
                        result = session.run(cypher, 
                                           source=row['source'], 
                                           target=row['target'],
                                           metaedge=row['metaedge'])
                        if result.single():
                            edges_created += 1
                    except Exception:
                        continue
                
                total_created += edges_created
                if (i // batch_size) % 10 == 0:
                    logger.info(f"Created {total_created} edges so far...")
        
        logger.info(f"Successfully loaded {total_created} edges")
        return total_created
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        with self.driver.session() as session:
            total_nodes = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
            total_rels = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
            
            # Count by type
            node_counts = {}
            result = session.run("MATCH (n:HetionetNode) RETURN n.kind as kind, count(n) as count")
            for record in result:
                node_counts[record["kind"]] = record["count"]
            
            return {
                "total_nodes": total_nodes,
                "total_relationships": total_rels,
                "nodes_by_type": node_counts
            }

def main():
    """Main function to load clinical trial diseases"""
    
    # Load environment variables
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
    
    # Configuration
    NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://your-instance.databases.neo4j.io")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your-password")
    
    # File paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    datasets_dir = os.path.join(script_dir, "..", "datasets")
    
    clinical_trials_file = os.path.join(datasets_dir, "clinical_trials.csv")
    nodes_file = os.path.join(datasets_dir, "hetionet-v1.0-nodes.tsv")
    edges_file = os.path.join(datasets_dir, "hetionet-v1.0-edges.sif")
    
    # Check if files exist
    for file_path in [clinical_trials_file, nodes_file, edges_file]:
        if not os.path.exists(file_path):
            logger.error(f"Required file not found: {file_path}")
            return
    
    # Initialize loader
    loader = None
    try:
        logger.info("=== Initializing Neo4j connection ===")
        loader = ClinicalTrialNeo4jLoader(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
        
        # Step 1: Extract diseases from clinical trials
        logger.info("=== Extracting diseases from clinical trials ===")
        diseases = loader.extract_diseases_from_clinical_trials(clinical_trials_file)
        
        # Step 2: Match diseases in Hetionet
        logger.info("=== Matching diseases in Hetionet ===")
        matched_disease_nodes = loader.match_diseases_in_hetionet(diseases, nodes_file)
        disease_ids = {d['id'] for d in matched_disease_nodes}
        
        if not disease_ids:
            logger.error("No diseases matched in Hetionet!")
            return
        
        # Step 3: Get related nodes and edges
        logger.info("=== Getting related nodes and edges ===")
        related_nodes, related_edges = loader.get_related_nodes_and_edges(
            disease_ids, nodes_file, edges_file
        )
        
        # Step 4: Clear database
        logger.info("=== Clearing existing data ===")
        loader.clear_database()
        
        # Step 5: Create constraints and indexes
        logger.info("=== Creating constraints and indexes ===")
        loader.create_constraints_and_indexes()
        
        # Step 6: Load nodes
        logger.info("=== Loading nodes ===")
        start_time = time.time()
        nodes_loaded = loader.load_nodes(related_nodes)
        nodes_time = time.time() - start_time
        
        # Step 7: Load edges
        logger.info("=== Loading edges ===")
        start_time = time.time()
        edges_loaded = loader.load_edges(related_edges)
        edges_time = time.time() - start_time
        
        # Step 8: Get final statistics
        logger.info("=== Getting database statistics ===")
        stats = loader.get_database_stats()
        
        # Display summary
        logger.info("=== Loading Summary ===")
        logger.info(f"Clinical trials diseases: {len(diseases)}")
        logger.info(f"Matched Hetionet diseases: {len(disease_ids)}")
        logger.info(f"Total nodes loaded: {stats['total_nodes']}")
        logger.info(f"Total relationships loaded: {stats['total_relationships']}")
        logger.info(f"Loading time - Nodes: {nodes_time:.2f}s, Edges: {edges_time:.2f}s")
        
        logger.info("Node distribution:")
        for node_type, count in stats['nodes_by_type'].items():
            logger.info(f"  {node_type}: {count}")
        
        logger.info("Clinical trial diseases loaded successfully into Neo4j!")
        
    except Exception as e:
        logger.error(f"Error during loading process: {e}")
        raise
    finally:
        if loader:
            loader.close()

if __name__ == "__main__":
    main()
