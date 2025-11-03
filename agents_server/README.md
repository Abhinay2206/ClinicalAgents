# Clinical Agents with Gemini 2.5 Flash

A multi-agent system for clinical trial analysis using Google's Gemini 2.5 Flash model.

## Overview

This system consists of four specialized agents:

1. **Enrollment Agent**: Analyzes patient enrollment patterns using ChromaDB (when configured) or a local FAISS index + CSV fallback on clinical trials data
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

# MongoDB (optional, recommended for memory & audit logs)
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=ClinicalAgents

# Enable HumanProxyAgent (routes through Reasoner -> Reviewer -> Output)
USE_PROXY=1
```

### 3. Data Files

Local fallback for Enrollment Agent expects the following in `datasets/`:
- `clinical_trials.faiss` - FAISS index for enrollment analysis (optional; if missing, a transient index will be built from CSV)
- `clinical_trials.csv` - Clinical trials metadata (used to build prompts and to build a transient index when needed)

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

### Chatbot with Memory, Review, and Replay

```bash
python chatbot.py
```

Interactive commands:
- `session` — show current session id
- `session new` — start a new session
- `replay [<session_id>]` — print audit events for the session (requires MongoDB)

### REST API (FastAPI)

Start the API:

```bash
uvicorn agents_server.api:app --reload --port 8000
```

Endpoints:
- `POST /chat` body `{ "prompt": "...", "session_id": "optional" }`
- `GET /history/{session_id}`
- `GET /replay/{session_id}`

### Snapshot cadence

Control how often snapshots are written with `SNAPSHOT_EVERY` (default `1` — every turn). Set in `.env`:

```bash
SNAPSHOT_EVERY=3
```

### Test Individual Agents

```bash
python test_agents.py
```

## Agent Details

### Enrollment Agent
- Uses ChromaDB Cloud to find similar clinical trials when `CHROMA_*` env vars are set
- Falls back to a local FAISS index and `clinical_trials.csv` if Chroma is not configured
- Analyzes enrollment patterns and provides recruitment recommendations
- Data source: `datasets/clinical_trials.faiss` and `datasets/clinical_trials.csv` (or a transient FAISS index built at runtime)

### Efficacy Agent
- Connects to Neo4j graph database using environment variables when available
- If Neo4j is not configured, performs a general LLM-based efficacy analysis
- Environment variables (optional but recommended): NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

### Safety Agent
- Uses FDA Drug Label API: `https://api.fda.gov/drug/label.json`
- Searches by generic drug name: `openfda.generic_name:"{drug_name}"`
- Analyzes warnings, contraindications, adverse reactions, and drug interactions

### Planning Agent
- Coordinates all three specialist agents
- Synthesizes results into comprehensive analysis
- Uses Gemini 2.5 Flash for final reasoning

### Human Proxy, Reasoner, and Reviewer
- **HumanProxyAgent**: main interface; persists chat memory and audit logs in MongoDB; routes to agents and applies review gate before final output; supports replay.
- **ReasonerAgent**: produces structured output with `answer`, concise `steps`, `citations`, `used_agents`, and `confidence`.
- **ReviewerAgent**: validates accuracy, clarity, and consistency; can request revision or approve.

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
2. **Gemini API Errors**: Check your `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) in `.env`
3. **Neo4j Optional**: If not set, EfficacyAgent will still run with general analysis
4. **Enrollment Fallback**: If ChromaDB is not configured, the system will use local `datasets/clinical_trials.csv` and `datasets/clinical_trials.faiss` (or build a transient index)
5. **FDA API Errors**: Check internet connectivity (no API key needed)

## Model Information

- **Primary Model**: Gemini 2.0 Flash Experimental
- **Fallback**: You can change the model in `gemini_client.py` constructor
- **Context Window**: Large context window suitable for comprehensive analysis
- **Temperature**: Default 0.7 for balanced creativity and accuracy