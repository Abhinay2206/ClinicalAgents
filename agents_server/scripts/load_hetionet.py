import pandas as pd
import os
from neo4j import GraphDatabase
import logging
from typing import Dict, List, Optional
import time
from tqdm import tqdm
from dotenv import load_dotenv
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FilteredHetionetNeo4jLoader:
    """Load filtered Hetionet data into Neo4j AuraDB for clinical applications"""
    
    def __init__(self, uri: str, username: str, password: str):
        """
        Initialize connection to Neo4j AuraDB
        
        Args:
            uri: Neo4j AuraDB URI (e.g., "neo4j+s://xxxxx.databases.neo4j.io")
            username: Neo4j username
            password: Neo4j password
        """
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.verify_connection()
    
    def verify_connection(self):
        """Verify connection to Neo4j database"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                if test_value == 1:
                    logger.info("Successfully connected to Neo4j AuraDB")
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
            # Primary constraint for all nodes
            "CREATE CONSTRAINT hetionet_node_id IF NOT EXISTS FOR (n:HetionetNode) REQUIRE n.id IS UNIQUE",
            
            # Indexes for performance
            "CREATE INDEX hetionet_node_kind IF NOT EXISTS FOR (n:HetionetNode) ON (n.kind)",
            "CREATE INDEX hetionet_node_name IF NOT EXISTS FOR (n:HetionetNode) ON (n.name)",
            
            # Specific node type constraints
            "CREATE CONSTRAINT disease_id IF NOT EXISTS FOR (n:Disease) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT compound_id IF NOT EXISTS FOR (n:Compound) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT gene_id IF NOT EXISTS FOR (n:Gene) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT anatomy_id IF NOT EXISTS FOR (n:Anatomy) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT symptom_id IF NOT EXISTS FOR (n:Symptom) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT side_effect_id IF NOT EXISTS FOR (n:SideEffect) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT pathway_id IF NOT EXISTS FOR (n:Pathway) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT pharmacologic_class_id IF NOT EXISTS FOR (n:PharmacologicClass) REQUIRE n.id IS UNIQUE",
        ]
        
        with self.driver.session() as session:
            for constraint_or_index in constraints_and_indexes:
                try:
                    session.run(constraint_or_index)
                except Exception as e:
                    if "already exists" in str(e).lower() or "equivalent" in str(e).lower():
                        continue  # Constraint/index already exists
                    else:
                        logger.warning(f"Could not create constraint/index: {e}")
        
        logger.info("Constraints and indexes created")
    
    def load_filtered_nodes(self, nodes_file_path: str, batch_size: int = 1000):
        """
        Load filtered nodes from TSV file into Neo4j
        
        Args:
            nodes_file_path: Path to filtered_hetionet_nodes.tsv
            batch_size: Number of nodes to process in each batch
        """
        logger.info(f"Loading filtered nodes from {nodes_file_path}")
        
        try:
            # Read nodes file
            df_nodes = pd.read_csv(nodes_file_path, sep='\t')
            logger.info(f"Found {len(df_nodes)} filtered nodes")
            
            # Log node type distribution
            node_types = df_nodes['kind'].value_counts()
            logger.info("Node type distribution:")
            for node_type, count in node_types.items():
                logger.info(f"  {node_type}: {count}")
            
            # Process in batches
            total_created = 0
            with self.driver.session() as session:
                for i in range(0, len(df_nodes), batch_size):
                    batch = df_nodes.iloc[i:i+batch_size]
                    nodes_data = []
                    
                    for _, row in batch.iterrows():
                        nodes_data.append({
                            'id': row['id'],
                            'name': row['name'],
                            'kind': row['kind']
                        })
                    
                    # Create nodes with multiple labels
                    cypher = """
                    UNWIND $nodes AS node
                    CALL {
                        WITH node
                        CALL apoc.create.node(['HetionetNode', node.kind], {
                            id: node.id,
                            name: node.name,
                            kind: node.kind
                        }) YIELD node AS created_node
                        RETURN created_node
                    }
                    RETURN count(*)
                    """
                    
                    try:
                        result = session.run(cypher, nodes=nodes_data)
                        nodes_created = result.single()[0]
                    except Exception:
                        # Fallback: create nodes without APOC
                        nodes_created = 0
                        for node_data in nodes_data:
                            try:
                                simple_cypher = f"""
                                CREATE (n:HetionetNode:{node_data['kind']} {{
                                    id: $id,
                                    name: $name,
                                    kind: $kind
                                }})
                                """
                                session.run(simple_cypher, **node_data)
                                nodes_created += 1
                            except Exception as e:
                                logger.warning(f"Could not create node {node_data['id']}: {e}")
                    
                    total_created += nodes_created
                    logger.info(f"Created {nodes_created} nodes (batch {i//batch_size + 1}/{(len(df_nodes)-1)//batch_size + 1})")
            
            logger.info(f"Successfully loaded {total_created} filtered nodes")
            
        except Exception as e:
            logger.error(f"Error loading nodes: {e}")
            raise
    
    def load_filtered_edges(self, edges_file_path: str, batch_size: int = 2000):
        """
        Load filtered edges from SIF file into Neo4j
        
        Args:
            edges_file_path: Path to filtered_hetionet_edges.sif
            batch_size: Number of edges to process in each batch
        """
        logger.info(f"Loading filtered edges from {edges_file_path}")
        
        try:
            # Read edges file
            df_edges = pd.read_csv(edges_file_path, sep='\t')
            logger.info(f"Found {len(df_edges)} filtered edges")
            
            # Log edge type distribution
            edge_types = df_edges['metaedge'].value_counts()
            logger.info("Edge type distribution:")
            for edge_type, count in edge_types.head(15).items():  # Show top 15
                logger.info(f"  {edge_type}: {count}")
            
            # Process in batches
            total_created = 0
            failed_edges = 0
            
            with self.driver.session() as session:
                for i in range(0, len(df_edges), batch_size):
                    batch = df_edges.iloc[i:i+batch_size]
                    edges_data = []
                    
                    for _, row in batch.iterrows():
                        edges_data.append({
                            'source': row['source'],
                            'target': row['target'],
                            'metaedge': row['metaedge']
                        })
                    
                    # Create relationships - try APOC first, fallback to simple approach
                    try:
                        # Using APOC for dynamic relationship types
                        cypher = """
                        UNWIND $edges AS edge
                        MATCH (source:HetionetNode {id: edge.source})
                        MATCH (target:HetionetNode {id: edge.target})
                        CALL apoc.create.relationship(source, edge.metaedge, {}, target) YIELD rel
                        RETURN count(rel)
                        """
                        result = session.run(cypher, edges=edges_data)
                        edges_created = result.single()[0]
                        
                    except Exception as apoc_error:
                        # Fallback: create relationships with generic type and metaedge property
                        edges_created = 0
                        for edge_data in edges_data:
                            try:
                                fallback_cypher = """
                                MATCH (source:HetionetNode {id: $source})
                                MATCH (target:HetionetNode {id: $target})
                                CREATE (source)-[r:HETIONET_EDGE {metaedge: $metaedge}]->(target)
                                RETURN r
                                """
                                result = session.run(fallback_cypher, 
                                                   source=edge_data['source'], 
                                                   target=edge_data['target'],
                                                   metaedge=edge_data['metaedge'])
                                if result.single():
                                    edges_created += 1
                            except Exception:
                                failed_edges += 1
                                continue
                    
                    total_created += edges_created
                    
                    if i % (batch_size * 10) == 0:  # Log every 10 batches
                        logger.info(f"Created {edges_created} relationships (batch {i//batch_size + 1}/{(len(df_edges)-1)//batch_size + 1}), total: {total_created}")
            
            logger.info(f"Successfully loaded {total_created} relationships")
            if failed_edges > 0:
                logger.warning(f"Failed to create {failed_edges} relationships (nodes may not exist)")
            
        except Exception as e:
            logger.error(f"Error loading edges: {e}")
            raise
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        logger.info("Getting database statistics...")
        
        with self.driver.session() as session:
            # Count nodes by type
            node_counts = {}
            result = session.run("MATCH (n:HetionetNode) RETURN n.kind as kind, count(n) as count")
            for record in result:
                node_counts[record["kind"]] = record["count"]
            
            # Count relationships by type
            rel_counts = {}
            try:
                # Try to get metaedge types if using APOC
                result = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType")
                rel_types = [record["relationshipType"] for record in result]
                
                for rel_type in rel_types:
                    result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
                    rel_counts[rel_type] = result.single()["count"]
            except Exception:
                # Fallback: count by metaedge property
                result = session.run("MATCH ()-[r:HETIONET_EDGE]->() RETURN r.metaedge as metaedge, count(r) as count")
                for record in result:
                    rel_counts[record["metaedge"]] = record["count"]
            
            # Total counts
            total_nodes = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
            total_rels = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
            
            stats = {
                "total_nodes": total_nodes,
                "total_relationships": total_rels,
                "nodes_by_type": node_counts,
                "relationships_by_type": rel_counts
            }
            
            return stats

def main():
    """Main function to load filtered Hetionet data"""
    
    # Load environment variables
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
    
    # Configuration from environment variables
    NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://your-instance.databases.neo4j.io")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your-password")
    
    # Batch sizes from environment or defaults
    nodes_batch_size = int(os.getenv("NODES_BATCH_SIZE", "1000"))
    edges_batch_size = int(os.getenv("EDGES_BATCH_SIZE", "2000"))
    
    # File paths - use filtered data
    script_dir = os.path.dirname(os.path.abspath(__file__))
    datasets_dir = os.path.join(script_dir, "..", "datasets")
    filtered_dir = os.path.join(datasets_dir, "filtered")
    
    nodes_file = os.path.join(filtered_dir, "filtered_hetionet_nodes.tsv")
    edges_file = os.path.join(filtered_dir, "filtered_hetionet_edges.sif")
    
    # Check if filtered files exist
    if not os.path.exists(nodes_file) or not os.path.exists(edges_file):
        logger.error("Filtered Hetionet files not found. Please run filter_hetionet_for_clinical_trials.py first.")
        logger.error(f"Expected files: {nodes_file}, {edges_file}")
        return
    
    # Initialize loader
    loader = None
    try:
        logger.info("=== Initializing Neo4j connection ===")
        loader = FilteredHetionetNeo4jLoader(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
        
        # Clear existing data
        logger.info("=== Clearing existing data ===")
        loader.clear_database()
        
        # Create constraints and indexes
        logger.info("=== Creating constraints and indexes ===")
        loader.create_constraints_and_indexes()
        
        # Load filtered nodes
        logger.info("=== Loading filtered nodes ===")
        start_time = time.time()
        loader.load_filtered_nodes(nodes_file, batch_size=nodes_batch_size)
        nodes_time = time.time() - start_time
        
        # Load filtered edges
        logger.info("=== Loading filtered edges ===")
        start_time = time.time()
        loader.load_filtered_edges(edges_file, batch_size=edges_batch_size)
        edges_time = time.time() - start_time
        
        # Get final statistics
        logger.info("=== Getting database statistics ===")
        stats = loader.get_database_stats()
        
        # Display summary
        logger.info("=== Loading Summary ===")
        logger.info(f"Total nodes loaded: {stats['total_nodes']}")
        logger.info(f"Total relationships loaded: {stats['total_relationships']}")
        logger.info(f"Loading time - Nodes: {nodes_time:.2f}s, Edges: {edges_time:.2f}s")
        
        logger.info("Node distribution:")
        for node_type, count in stats['nodes_by_type'].items():
            logger.info(f"  {node_type}: {count}")
        
        logger.info("Top relationship types:")
        sorted_rels = sorted(stats['relationships_by_type'].items(), key=lambda x: x[1], reverse=True)
        for rel_type, count in sorted_rels[:10]:
            logger.info(f"  {rel_type}: {count}")
        
        logger.info("Filtered Hetionet data loaded successfully into Neo4j AuraDB!")
        
    except Exception as e:
        logger.error(f"Error during loading process: {e}")
        raise
    finally:
        if loader:
            loader.close()

if __name__ == "__main__":
    main()