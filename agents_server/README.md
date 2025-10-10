# Clinical Agents with Gemini 2.5 Flash

A multi-agent system for clinical trial analysis using Google's Gemini 2.5 Flash model.

## Overview

This system consists of four specialized agents:

1. **Enrollment Agent**: Analyzes patient enrollment patterns using FAISS similarity search on clinical trials data
2. **Efficacy Agent**: Analyzes treatment outcomes using Neo4j graph database
3. **Safety Agent**: Analyzes drug safety data using FDA API
4. **Planning Agent**: Coordinates all agents and synthesizes results

## Setup

### 1. Install Dependencies

```bash
cd agents_server
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual credentials:

```bash
# Gemini AI API Key (required)
GEMINI_API_KEY=your_gemini_api_key_here

# Neo4j Database (required for Efficacy Agent)
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password-here
```

### 3. Data Files

Ensure the following files exist in the `datasets/` folder:
- `clinical_trials.faiss` - FAISS index for enrollment analysis
- `clinical_trials_metadata.pkl` - Metadata for clinical trials

## Usage

### Basic Usage

```python
from main import run_pipeline
import numpy as np

# Create a query embedding (384 dimensions for sentence transformers)
query_embedding = np.random.rand(384).astype(np.float32)
query_embedding = query_embedding / np.linalg.norm(query_embedding)

# Run analysis
results = run_pipeline(query_embedding, "aspirin")

print("Final Summary:", results["final_summary"])
print("Sub-reports:", results["sub_reports"])
```

### Run the Complete Pipeline

```bash
python main.py
```

### Test Individual Agents

```bash
python test_agents.py
```

## Agent Details

### Enrollment Agent
- Uses FAISS index to find similar clinical trials
- Analyzes enrollment patterns and provides recruitment recommendations
- Data source: `datasets/clinical_trials.faiss` and `datasets/clinical_trials_metadata.pkl`

### Efficacy Agent
- Connects to Neo4j graph database using environment variables
- Analyzes treatment outcomes and efficacy metrics
- Requires: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD environment variables

### Safety Agent
- Uses FDA Drug Label API: `https://api.fda.gov/drug/label.json`
- Searches by generic drug name: `openfda.generic_name:"{drug_name}"`
- Analyzes warnings, contraindications, adverse reactions, and drug interactions

### Planning Agent
- Coordinates all three specialist agents
- Synthesizes results into comprehensive analysis
- Uses Gemini 2.5 Flash for final reasoning

## API Requirements

### Gemini API
- Get API key from Google AI Studio: https://makersuite.google.com/app/apikey
- Set as `GEMINI_API_KEY` environment variable

### Neo4j Database
- Create instance at https://console.neo4j.io/
- Set connection details in environment variables

### FDA API
- No API key required for drug label endpoint
- Rate limited but publicly accessible

## File Structure

```
agents_server/
├── main.py                 # Main pipeline runner
├── test_agents.py          # Individual agent tests
├── gemini_client.py        # Gemini 2.5 Flash wrapper
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── agents/
│   ├── base_agent.py      # Base agent class
│   ├── enrollment_agent.py # FAISS-based enrollment analysis
│   ├── efficacy_agent.py  # Neo4j-based efficacy analysis
│   ├── safety_agent.py    # FDA API-based safety analysis
│   ├── planning_agent.py  # Agent coordinator
│   └── resoning_agent.py  # Results synthesizer
└── datasets/
    ├── clinical_trials.faiss          # FAISS index
    ├── clinical_trials_metadata.pkl   # Trial metadata
    └── ...                           # Other data files
```

## Troubleshooting

1. **Import Errors**: Run `pip install -r requirements.txt`
2. **Gemini API Errors**: Check your `GEMINI_API_KEY` in `.env`
3. **Neo4j Errors**: Verify database credentials and connectivity
4. **FAISS Errors**: Ensure `datasets/clinical_trials.faiss` and `datasets/clinical_trials_metadata.pkl` exist
5. **FDA API Errors**: Check internet connectivity (no API key needed)

## Model Information

- **Primary Model**: Gemini 2.0 Flash Experimental
- **Fallback**: You can change the model in `gemini_client.py` constructor
- **Context Window**: Large context window suitable for comprehensive analysis
- **Temperature**: Default 0.7 for balanced creativity and accuracy