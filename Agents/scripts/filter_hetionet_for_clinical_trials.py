import pandas as pd
import numpy as np
import os
import re
import logging
from typing import Set, List, Dict, Tuple
from collections import defaultdict
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClinicalTrialsFilter:
    """Extract and normalize diseases and compounds from clinical trials data"""
    
    def __init__(self, clinical_trials_path: str):
        self.clinical_trials_path = clinical_trials_path
        self.df_trials = None
        
        # Common disease synonyms and mappings
        self.disease_synonyms = {
            'cancer': ['carcinoma', 'tumor', 'tumour', 'malignancy', 'neoplasm', 'adenocarcinoma'],
            'diabetes': ['diabetes mellitus', 'diabetic', 'dm'],
            'hypertension': ['high blood pressure', 'htn'],
            'covid-19': ['covid', 'coronavirus', 'sars-cov-2'],
            'alzheimer': ['alzheimer disease', 'dementia'],
            'parkinson': ['parkinson disease', 'pd'],
            'depression': ['major depressive disorder', 'mdd'],
            'schizophrenia': ['psychosis', 'psychotic'],
            'asthma': ['bronchial asthma'],
            'copd': ['chronic obstructive pulmonary disease'],
            'hiv': ['human immunodeficiency virus', 'aids'],
            'hepatitis': ['hepatitis b', 'hepatitis c', 'hbv', 'hcv'],
        }
        
        # Common drug name patterns and generic/brand mappings
        self.drug_patterns = {
            # Common suffixes for drug names
            'suffixes': ['-mab', '-nib', '-zumab', '-tinib', '-prazole', '-statin', '-cillin', '-mycin'],
            # Common prefixes
            'prefixes': ['anti-', 'pre-', 'pro-'],
        }
        
    def load_clinical_trials(self):
        """Load clinical trials data"""
        logger.info(f"Loading clinical trials data from {self.clinical_trials_path}")
        try:
            self.df_trials = pd.read_csv(self.clinical_trials_path)
            logger.info(f"Loaded {len(self.df_trials)} clinical trials")
        except Exception as e:
            logger.error(f"Error loading clinical trials: {e}")
            raise
    
    def extract_diseases_from_trials(self) -> Set[str]:
        """Extract disease terms from clinical trials data"""
        logger.info("Extracting diseases from clinical trials...")
        
        diseases = set()
        
        if self.df_trials is None:
            self.load_clinical_trials()
        
        # Extract from Disease column
        for disease in self.df_trials['Disease'].dropna():
            if isinstance(disease, str):
                # Clean and normalize
                disease_clean = disease.lower().strip()
                diseases.add(disease_clean)
                
                # Add synonyms
                for base_disease, synonyms in self.disease_synonyms.items():
                    if base_disease in disease_clean:
                        diseases.update(synonyms)
                        diseases.add(base_disease)
        
        # Extract from Conditions column
        for conditions in self.df_trials['Conditions'].dropna():
            if isinstance(conditions, str):
                # Split by common delimiters
                condition_list = re.split(r'[;,\n\|]', conditions.lower())
                for condition in condition_list:
                    condition = condition.strip()
                    if len(condition) > 3:  # Filter out very short terms
                        diseases.add(condition)
        
        # Extract from Eligibility Criteria (looking for disease mentions)
        for criteria in self.df_trials['Eligibility Criteria'].dropna():
            if isinstance(criteria, str):
                criteria_lower = criteria.lower()
                # Look for disease patterns
                disease_matches = re.findall(r'\b(?:cancer|carcinoma|tumor|disease|syndrome|disorder)\b', criteria_lower)
                diseases.update(disease_matches)
        
        logger.info(f"Extracted {len(diseases)} unique disease terms")
        return diseases
    
    def extract_compounds_from_trials(self) -> Set[str]:
        """Extract compound/drug terms from clinical trials data"""
        logger.info("Extracting compounds from clinical trials...")
        
        compounds = set()
        
        if self.df_trials is None:
            self.load_clinical_trials()
        
        # Common drug name patterns
        drug_patterns = [
            r'\b\w*mab\b',      # monoclonal antibodies (-mab)
            r'\b\w*nib\b',      # kinase inhibitors (-nib)
            r'\b\w*zumab\b',    # humanized antibodies (-zumab)
            r'\b\w*tinib\b',    # tyrosine kinase inhibitors (-tinib)
            r'\b\w*prazole\b',  # proton pump inhibitors (-prazole)
            r'\b\w*statin\b',   # statins
            r'\b\w*cillin\b',   # antibiotics (-cillin)
            r'\b\w*mycin\b',    # antibiotics (-mycin)
        ]
        
        # Search in eligibility criteria for drug mentions
        for criteria in self.df_trials['Eligibility Criteria'].dropna():
            if isinstance(criteria, str):
                criteria_lower = criteria.lower()
                
                # Look for drug patterns
                for pattern in drug_patterns:
                    matches = re.findall(pattern, criteria_lower)
                    compounds.update(matches)
                
                # Look for common drug keywords
                drug_keywords = ['treatment', 'therapy', 'medication', 'drug', 'compound', 'agent']
                for keyword in drug_keywords:
                    if keyword in criteria_lower:
                        # Extract words around the keyword (potential drug names)
                        context_matches = re.findall(rf'\b\w+\s+{keyword}|\b{keyword}\s+\w+', criteria_lower)
                        for match in context_matches:
                            words = match.split()
                            compounds.update([w for w in words if w != keyword and len(w) > 3])
        
        logger.info(f"Extracted {len(compounds)} potential compound terms")
        return compounds

class HetionetFilter:
    """Filter Hetionet data based on clinical trials entities"""
    
    def __init__(self, nodes_path: str, edges_path: str):
        self.nodes_path = nodes_path
        self.edges_path = edges_path
        self.df_nodes = None
        self.df_edges = None
        
    def load_hetionet_data(self):
        """Load Hetionet nodes and edges"""
        logger.info("Loading Hetionet data...")
        
        try:
            self.df_nodes = pd.read_csv(self.nodes_path, sep='\t')
            logger.info(f"Loaded {len(self.df_nodes)} Hetionet nodes")
            
            # Load edges in chunks due to size
            self.df_edges = pd.read_csv(self.edges_path, sep='\t')
            logger.info(f"Loaded {len(self.df_edges)} Hetionet edges")
            
        except Exception as e:
            logger.error(f"Error loading Hetionet data: {e}")
            raise
    
    def find_matching_nodes(self, clinical_terms: Set[str], node_types: List[str]) -> Set[str]:
        """Find Hetionet nodes that match clinical trial terms"""
        logger.info(f"Finding matching nodes for {len(clinical_terms)} clinical terms in types: {node_types}")
        
        if self.df_nodes is None:
            self.load_hetionet_data()
        
        matching_node_ids = set()
        
        # Filter nodes by type
        type_filtered_nodes = self.df_nodes[self.df_nodes['kind'].isin(node_types)]
        logger.info(f"Filtering from {len(type_filtered_nodes)} nodes of types: {node_types}")
        
        for _, node in type_filtered_nodes.iterrows():
            node_name = str(node['name']).lower()
            node_id = node['id']
            
            # Check for exact matches or partial matches
            for clinical_term in clinical_terms:
                clinical_term_clean = clinical_term.lower().strip()
                
                # Exact match
                if clinical_term_clean == node_name:
                    matching_node_ids.add(node_id)
                    logger.debug(f"Exact match: {clinical_term_clean} -> {node_name}")
                
                # Partial match (clinical term contains node name or vice versa)
                elif (clinical_term_clean in node_name or 
                      node_name in clinical_term_clean or
                      any(word in node_name for word in clinical_term_clean.split() if len(word) > 3)):
                    matching_node_ids.add(node_id)
                    logger.debug(f"Partial match: {clinical_term_clean} -> {node_name}")
        
        logger.info(f"Found {len(matching_node_ids)} matching nodes")
        return matching_node_ids
    
    def filter_nodes_and_edges(self, relevant_node_ids: Set[str], output_dir: str):
        """Filter and save relevant nodes and edges"""
        logger.info(f"Filtering nodes and edges for {len(relevant_node_ids)} relevant nodes")
        
        if self.df_nodes is None or self.df_edges is None:
            self.load_hetionet_data()
        
        # Filter nodes
        filtered_nodes = self.df_nodes[self.df_nodes['id'].isin(relevant_node_ids)]
        
        # Filter edges (keep edges where both source and target are in relevant nodes)
        logger.info("Filtering edges...")
        filtered_edges = self.df_edges[
            (self.df_edges['source'].isin(relevant_node_ids)) & 
            (self.df_edges['target'].isin(relevant_node_ids))
        ]
        
        # Also include edges connected to relevant nodes (one hop)
        logger.info("Adding one-hop connections...")
        one_hop_edges = self.df_edges[
            (self.df_edges['source'].isin(relevant_node_ids)) | 
            (self.df_edges['target'].isin(relevant_node_ids))
        ]
        
        # Get additional nodes from one-hop edges
        additional_node_ids = set(one_hop_edges['source'].tolist() + one_hop_edges['target'].tolist())
        additional_nodes = self.df_nodes[self.df_nodes['id'].isin(additional_node_ids)]
        
        # Combine original and additional nodes
        final_nodes = pd.concat([filtered_nodes, additional_nodes]).drop_duplicates()
        final_edges = one_hop_edges
        
        # Save filtered data
        os.makedirs(output_dir, exist_ok=True)
        
        nodes_output_path = os.path.join(output_dir, "filtered_hetionet_nodes.tsv")
        edges_output_path = os.path.join(output_dir, "filtered_hetionet_edges.sif")
        
        final_nodes.to_csv(nodes_output_path, sep='\t', index=False)
        final_edges.to_csv(edges_output_path, sep='\t', index=False)
        
        logger.info(f"Saved {len(final_nodes)} filtered nodes to {nodes_output_path}")
        logger.info(f"Saved {len(final_edges)} filtered edges to {edges_output_path}")
        
        # Save summary statistics
        summary = {
            "original_nodes": len(self.df_nodes),
            "original_edges": len(self.df_edges),
            "filtered_nodes": len(final_nodes),
            "filtered_edges": len(final_edges),
            "relevant_seed_nodes": len(relevant_node_ids),
            "node_types": final_nodes['kind'].value_counts().to_dict(),
            "edge_types": final_edges['metaedge'].value_counts().to_dict()
        }
        
        summary_path = os.path.join(output_dir, "filtering_summary.json")
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Saved filtering summary to {summary_path}")
        
        return final_nodes, final_edges, summary

def main():
    """Main function to filter Hetionet data based on clinical trials"""
    
    # File paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    datasets_dir = os.path.join(script_dir, "..", "datasets")
    
    clinical_trials_path = os.path.join(datasets_dir, "clinical_trials.csv")
    hetionet_nodes_path = os.path.join(datasets_dir, "hetionet-v1.0-nodes.tsv")
    hetionet_edges_path = os.path.join(datasets_dir, "hetionet-v1.0-edges.sif")
    output_dir = os.path.join(datasets_dir, "filtered")
    
    # Verify files exist
    for file_path in [clinical_trials_path, hetionet_nodes_path, hetionet_edges_path]:
        if not os.path.exists(file_path):
            logger.error(f"Required file not found: {file_path}")
            return
    
    try:
        # Step 1: Extract entities from clinical trials
        logger.info("=== Step 1: Extracting entities from clinical trials ===")
        trials_filter = ClinicalTrialsFilter(clinical_trials_path)
        
        diseases = trials_filter.extract_diseases_from_trials()
        compounds = trials_filter.extract_compounds_from_trials()
        
        logger.info(f"Extracted {len(diseases)} disease terms and {len(compounds)} compound terms")
        
        # Step 2: Find matching Hetionet nodes
        logger.info("=== Step 2: Finding matching Hetionet nodes ===")
        hetionet_filter = HetionetFilter(hetionet_nodes_path, hetionet_edges_path)
        
        # Find disease nodes
        disease_nodes = hetionet_filter.find_matching_nodes(diseases, ['Disease'])
        
        # Find compound nodes
        compound_nodes = hetionet_filter.find_matching_nodes(compounds, ['Compound'])
        
        # Combine all relevant nodes
        all_relevant_nodes = disease_nodes.union(compound_nodes)
        
        logger.info(f"Found {len(disease_nodes)} disease nodes and {len(compound_nodes)} compound nodes")
        logger.info(f"Total relevant nodes: {len(all_relevant_nodes)}")
        
        # Step 3: Filter and save data
        logger.info("=== Step 3: Filtering and saving data ===")
        filtered_nodes, filtered_edges, summary = hetionet_filter.filter_nodes_and_edges(
            all_relevant_nodes, output_dir
        )
        
        # Display summary
        logger.info("=== Filtering Summary ===")
        logger.info(f"Original: {summary['original_nodes']} nodes, {summary['original_edges']} edges")
        logger.info(f"Filtered: {summary['filtered_nodes']} nodes, {summary['filtered_edges']} edges")
        logger.info(f"Reduction: {(1 - summary['filtered_nodes']/summary['original_nodes'])*100:.1f}% nodes, "
                   f"{(1 - summary['filtered_edges']/summary['original_edges'])*100:.1f}% edges")
        
        logger.info("Node types in filtered data:")
        for node_type, count in summary['node_types'].items():
            logger.info(f"  {node_type}: {count}")
        
        logger.info("Top edge types in filtered data:")
        top_edges = sorted(summary['edge_types'].items(), key=lambda x: x[1], reverse=True)[:10]
        for edge_type, count in top_edges:
            logger.info(f"  {edge_type}: {count}")
        
        logger.info("Filtering completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during filtering process: {e}")
        raise

if __name__ == "__main__":
    main()