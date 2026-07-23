# Code Archaeologist

> **An LLM-Based Temporal RAG System for GitHub Repository Evolution Intelligence**

Code Archaeologist is an AI-powered software repository mining and evolution intelligence system. It combines **Time-Aware Retrieval-Augmented Generation (Temporal RAG)**, persistent vector storage (**ChromaDB**), local LLM inference (**Ollama / DeepSeek Coder**), and multi-factor algorithmic scoring to provide deep architectural insights into codebase history.

---

## 🌟 Key Features

1. **Repository Ingestion & Temporal Indexing:**
   - Shallow and deep Git commit history extraction via `GitPython`.
   - Time-stamped commit vector snapshot embedding using `sentence-transformers` (`all-MiniLM-L6-v2`) in `ChromaDB`.
   - Automatic language composition detection.

2. **Automated Repository Intelligence Dashboard:**
   - **Repository Health Score (0-100):** Evaluates commit consistency, code churn, author distribution, and hotspot stability.
   - **Developer Bus Factor Analytics:** Recharts visualizations of contributor commit counts and ownership share percentages.
   - **Hotspot & Churn Heatmap:** Identifies high-risk files with frequent revisions, multi-author churn, and architecture tags.
   - **Co-Evolving Files (Logical Coupling):** Discovers pairs of files that change together across commits.
   - **AI Executive Summary:** Automated architectural health synthesis.

3. **Evolution Timeline:**
   - Chronological commit milestone visualization with interactive filters (Search, Author, File scope, Architecture changes only).
   - Uniform lifespan commit sampling for macro-evolutionary narrative synthesis.

4. **Forensic Bug Origin Analysis:**
   - Locates the commit most likely responsible for introducing a bug or regression given a natural language query or error description.
   - Multi-factor weighted confidence scoring formula:
     - **Semantic Similarity:** 40%
     - **File Scope Match:** 20%
     - **Temporal Context & Recency:** 15%
     - **Architecture Impact:** 10%
     - **Commit Importance:** 10%
     - **Developer Activity Frequency:** 5%
   - Visual regression timeline propagation (`Supporting Commits → Suspected Bug Introduction → Current HEAD`).

5. **Repository Chat & Causal Reasoning:**
   - **Repo Chat Mode:** Natural language Q&A grounded in time-aware commit snapshots with evidence citations.
   - **Causal Reasoning Mode:** Infer design rationale ("Why was X changed?").

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & **npm**
- **Ollama** (Running locally with `deepseek-coder-v2` or `llama3`)

---

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the FastAPI server:
   ```bash
   python -m uvicorn main:app --reload --port 8000
   ```
   The backend API will be available at `http://localhost:8000`.

---

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Start Vite development server:
   ```bash
   npm run dev
   ```
   The application will be accessible at `http://localhost:5173`.

---

## 🏗️ Project Architecture

```
code-archaeologist/
├── backend/
│   ├── main.py                    # FastAPI Entry & Router mounts
│   ├── requirements.txt           # Backend dependencies
│   └── app/
│       ├── api/routes/            # REST API Routes
│       │   ├── repo.py            # Repository Ingestion & Intelligence
│       │   ├── chat.py            # Conversational Q&A & Causal Reasoning
│       │   ├── evolution.py       # Evolution Narrative Generation
│       │   └── analysis.py        # Forensic Bug Origin Analysis
│       ├── core/                  # Configuration & Logging
│       ├── ingestion/             # Git Repository Mining
│       ├── models/                # Pydantic Schemas
│       ├── parsing/               # Code & AST Parsing Roadmap
│       ├── reasoning/             # Intelligence, Bug Analysis & Scorer
│       └── temporal_rag/          # ChromaDB & Vector Embeddings
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx                # Sidebar Navigation & Router
│       ├── services/api.js        # Axios API Client Layer
│       ├── store/repoStore.jsx    # React Context State
│       ├── pages/                 # Full Page Views
│       └── components/            # Visual UI Components
│           ├── timeline/
│           ├── bug_origin/
│           └── intelligence/
├── docs/                          # Project Documentation
└── docker-compose.yml
```

---

## 📄 License
This project is developed for AI research and educational software engineering evaluation.
