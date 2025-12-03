# ClinicalAgents 🏥

**ClinicalAgents** is an advanced AI-powered multi-agent system designed to revolutionize how healthcare professionals and researchers interact with clinical trial data and drug safety information. By leveraging Large Language Models (LLMs) and a dynamic orchestration framework, it automates complex tasks such as trial enrollment analysis and drug safety assessment.

![Architecture](docs/architecture.png)

## 🌟 Key Features

### 🤖 Multi-Agent System
- **Enrollment Agent**: Intelligent matching of patients to clinical trials using hybrid search (Semantic + Keyword) and success prediction algorithms.
- **Safety Agent**: Comprehensive analysis of drug safety profiles, integrating real-time FDA data for black box warnings and adverse events.
- **Efficacy Agent**: Analyzes trial results to determine treatment efficacy (in development).
- **Human Proxy Agent**: Facilitates human-in-the-loop decision-making for critical or ambiguous queries.

### 💬 Intelligent Chat Interface
- **Context-Aware Conversations**: Maintains session history for continuous, natural dialogue.
- **Dynamic Orchestration**: Automatically routes user queries to the most relevant specialist agent.
- **Rich Responses**: Provides structured, easy-to-read medical insights with citations and visual indicators.

### 🔐 Secure & Personalized
- **User Authentication**: Secure registration and login system.
- **Session Management**: Create, rename, and delete chat sessions to organize your research.
- **Persistent History**: All interactions are saved to MongoDB for future reference.

## 🛠️ Technology Stack

### Backend (`agents_server`)
- **Framework**: FastAPI (Python)
- **LLM**: Google Gemini Pro
- **Database**: MongoDB (User/Session data), ChromaDB & FAISS (Vector Search)
- **External APIs**: ClinicalTrials.gov, openFDA
- **Orchestration**: Custom Dynamic Planner

### Frontend (`client`)
- **Framework**: Next.js 16 (React 19)
- **Styling**: Tailwind CSS 4
- **UI Components**: Heroicons, Framer Motion
- **State Management**: React Hooks

## 📂 Project Structure

```
ClinicalAgent/
├── agents_server/          # Python FastAPI Backend
│   ├── agents/             # Autonomous Agent Implementations
│   ├── storage/            # Database Connectors
│   ├── datasets/           # Local Clinical Data
│   ├── app.py              # API Entry Point
│   └── simple_dynamic_orchestrator.py # Agent Planner
│
├── client/                 # Next.js Frontend
│   ├── app/                # App Router Pages
│   ├── components/         # Reusable UI Components
│   ├── hooks/              # Custom React Hooks
│   └── services/           # API Client Services
│
└── docs/                   # Documentation & Assets
```

## 🚀 Getting Started

For detailed installation and setup instructions, please refer to the **[SETUP.md](SETUP.md)** file.

### Quick Start
1.  **Backend**:
    ```bash
    cd agents_server
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python app.py
    ```
2.  **Frontend**:
    ```bash
    cd client
    npm install
    npm run dev
    ```

## 🔌 API Documentation

Once the backend is running, you can access the interactive API documentation (Swagger UI) at:
`http://localhost:8000/docs`

### Key Endpoints
- `POST /chat`: Send a message to the agent system.
- `POST /auth/login`: Authenticate a user.
- `GET /sessions`: Retrieve user chat sessions.
- `GET /history/{session_id}`: Get message history for a session.
