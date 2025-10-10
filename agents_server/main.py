# main.py
import os
import numpy as np
from dotenv import load_dotenv
from agents.planning_agent import PlanningAgent
from agents.resoning_agent import ReasoningAgent
from gemini_client import GeminiClient

# Load environment variables
load_dotenv()

def run_pipeline(query_embedding, drug_name):
    try:
        # Initialize Gemini 2.5 Flash model
        llm = GeminiClient(model_name="gemini-2.0-flash-exp")
        
        # Initialize agents
        planner = PlanningAgent(llm)
        reasoner = ReasoningAgent(llm)

        # Execute analysis plan
        reports = planner.execute_plan(query_embedding, drug_name)
        final_summary = reasoner.synthesize(reports)

        return {"sub_reports": reports, "final_summary": final_summary}
    
    except Exception as e:
        return {"error": f"Pipeline execution failed: {str(e)}"}

def create_sample_embedding(dimension=384):
    embedding = np.random.rand(dimension).astype(np.float32)
    # Normalize the embedding
    embedding = embedding / np.linalg.norm(embedding)
    return embedding

def create_breast_cancer_embedding(dimension=384):
    # Use a seed for reproducible results that represent breast cancer characteristics
    np.random.seed(42)
    embedding = np.random.rand(dimension).astype(np.float32)
    # Normalize the embedding
    embedding = embedding / np.linalg.norm(embedding)
    return embedding

def save_results_to_file(results, patient_condition, output_dir="./outputs"):
    import datetime
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"clinical_trials_analysis_{patient_condition.lower().replace(' ', '_')}_{timestamp}.txt"
    filepath = os.path.join(output_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write(f"CLINICAL TRIALS ANALYSIS FOR {patient_condition.upper()}\n")
            f.write("="*80 + "\n")
            f.write(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Patient Condition: {patient_condition}\n")
            f.write("="*80 + "\n\n")
            
            if "error" in results:
                f.write(f"ERROR: {results['error']}\n")
            else:
                f.write("EXECUTIVE SUMMARY\n")
                f.write("-" * 40 + "\n")
                f.write(results["final_summary"])
                f.write("\n\n")
                
                f.write("DETAILED ANALYSIS REPORTS\n")
                f.write("-" * 40 + "\n\n")
                
                for report_type, report_content in results["sub_reports"].items():
                    f.write(f"{report_type.upper()} ANALYSIS\n")
                    f.write("=" * len(f"{report_type.upper()} ANALYSIS") + "\n")
                    f.write(report_content)
                    f.write("\n\n" + "-"*60 + "\n\n")
        
        return filepath
    except Exception as e:
        print(f"Error saving results to file: {e}")
        return None

if __name__ == "__main__":
    # Clinical trial analysis for breast cancer patient
    print("Clinical Agent Pipeline - Breast Cancer Trial Analysis")
    print("=" * 60)
    
    # Patient condition and related treatment
    patient_condition = "Breast Cancer"
    treatment_focus = "Breast Cancer Therapies"
    
    # Create breast cancer-specific query embedding
    breast_cancer_embedding = create_breast_cancer_embedding()
    
    print(f"Patient Condition: {patient_condition}")
    print(f"Treatment Focus: {treatment_focus}")
    print(f"Query embedding dimension: {len(breast_cancer_embedding)}")
    print("\nAnalyzing suitable clinical trials...")
    print("-" * 60)
    
    # Run the pipeline
    results = run_pipeline(breast_cancer_embedding, treatment_focus)
    
    # Save results to file
    output_file = save_results_to_file(results, patient_condition)
    
    if "error" in results:
        print(f"Error: {results['error']}")
    else:
        print("\n" + "="*60)
        print("ANALYSIS COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"Results saved to: {output_file}")
        print("\n" + "="*60)
        print("EXECUTIVE SUMMARY")
        print("="*60)
        print(results["final_summary"])
        
        print("\n" + "="*60)
        print("DETAILED ANALYSIS REPORTS")
        print("="*60)
        for report_type, report_content in results["sub_reports"].items():
            print(f"\n--- {report_type.upper()} ANALYSIS ---")
            print(report_content[:500] + "..." if len(report_content) > 500 else report_content)
        
        print(f"\n\nFull detailed analysis saved to: {output_file}")
