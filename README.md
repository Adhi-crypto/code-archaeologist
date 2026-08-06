# Code Archaeologist

> **An LLM-Based Temporal RAG Platform for Software Evolution Intelligence**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-009688.svg?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2-61DAFB.svg?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.0-646CFF.svg?style=flat-square&logo=vite&logoColor=white)](https://vitejs.dev/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.4%2B-FF6F00.svg?style=flat-square)](https://www.trychroma.com/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-black.svg?style=flat-square&logo=ollama&logoColor=white)](https://ollama.ai/)
[![License](https://img.shields.io/badge/License-Educational%20%26%20Research-green.svg?style=flat-square)](#-license)

---

## 📌 Project Overview

**Code Archaeologist** is an open-source, local-first software repository mining and evolution intelligence system. It bridges the gap between Large Language Models (LLMs) and software engineering history by implementing **Time-Aware Retrieval-Augmented Generation (Temporal RAG)**.

### The Problem

Traditional RAG systems treat code text as static documents. However, software codebases are dynamic, evolving entities. Questions such as _"Why was this refactoring introduced?"_, _"What changed in the second commit?"_, or _"Which commit introduced this bug?"_ cannot be answered by static vector search because traditional vector databases lack chronological sequence, commit diffs, and author attribution context.

### The Solution: Temporal RAG

Code Archaeologist extracts time-stamped commit snapshots, diff statistics, author activity, and architectural scope metadata into a high-dimensional vector store (**ChromaDB**). It uses a 3-stage temporal context retriever (Overview `repo_summary` $\rightarrow$ Positional `commit_index` $\rightarrow$ Cosine vector similarity) to ground LLM answers in verified software evolution history.

### Target Users

- **Software Architects & Tech Leads**: Inspect codebase health, author bus factor risks, and logical file coupling.
- **Developers & Code Reviewers**: Query commit evolution, understand past design rationale, and audit code diffs.
- **Forensic QA Engineers**: Pinpoint bug origins and root-cause commits via multi-factor weighted confidence scoring.

---

## 🌟 Key Features

### 📦 1. Repository Ingestion & Multi-Stage Indexing

- **Git Commit Mining**: Asynchronous commit history extraction via `GitPython` with `ThreadPoolExecutor` diff parallelization.
- **Time-Aware Embeddings**: Embeds commit snapshot metadata (`sha`, `author`, `timestamp_unix`, `files_changed`, `diff_summary`) into 384-dimensional dense vectors using `sentence-transformers` (`all-MiniLM-L6-v2`).
- **Deterministic Overview Indexing**: Indexes a dedicated `repo_summary` document (`id = {repo_id}_overview`) containing `README.md`, primary dependencies (`package.json`, `pyproject.toml`, `requirements.txt`), and directory trees.

### 💬 2. Conversational Chat & Causal Reasoning

- **Real-Time Token Streaming**: Streams response tokens live over Server-Sent Events (SSE) with `status`, `metadata`, `token`, and `done` events.
- **Intent Classification**: Dynamically routes queries to `OVERVIEW`, `HISTORICAL`, `IMPLEMENTATION`, `ARCHITECTURE`, or `BUG_ORIGIN` handlers.
- **Positional Resolution**: Detects ordinal queries (_"first commit"_, _"2nd commit"_, _"latest commit"_) and fetches exact `commit_index` snapshots directly.
- **Dynamic Score Evaluation**: Computes real-time **Evidence Match Score (%)** and **Answer Confidence (%)** post-retrieval without hardcoded fallbacks.

### 📊 3. Repository Intelligence Dashboard

- **Repository Health Score (0–100)**: Evaluates contributor equity, code churn stability, activity regularity, and hotspot risk.
- **Developer Bus Factor Analytics**: Visualizes author contribution shares and bus factor risks via Recharts.
- **Hotspot & Churn Heatmap**: Highlights critical files with frequent modifications, multi-author churn, and architectural tags.
- **Logical File Coupling**: Identifies pairs of files that co-evolve together across commits.

### ⏳ 4. Architectural Evolution Timeline

- Chronological commit milestone timeline with interactive search, author filtering, and architectural milestone toggles.
- **Uniform Milestone Sampling**: Step-based sampling ($S = \lceil N / 20 \rceil$) selecting representative commits for LLM macro-evolution narrative generation.

### 🔍 5. Forensic Bug Origin Analysis

- Multi-factor weighted confidence scoring algorithm to attribute bugs to root-cause commits:
  $$\text{Score} = (0.40 \cdot \text{Semantic}) + (0.20 \cdot \text{File Scope}) + (0.15 \cdot \text{Recency}) + (0.10 \cdot \text{Arch Impact}) + (0.10 \cdot \text{Importance}) + (0.05 \cdot \text{Dev Freq})$$

---

## 🏗️ System Architecture

```text
+-----------------------------------------------------------------------------------+
|                                 REACT + VITE FRONTEND                             |
|  [Ingestion Page]  [Repo Chat]  [Intelligence]  [Evolution]  [Bug Origin Forensic]  |
+----------------------------------------+------------------------------------------+
                                         |
                                         | HTTP REST / SSE Stream
                                         v
+-----------------------------------------------------------------------------------+
|                                FASTAPI ASGI BACKEND                               |
|   /api/repo/ingest    /api/chat/query-stream    /api/repo/intelligence            |
+--------------------+-------------------+-------------------+----------------------+
                     |                   |                   |
                     v                   v                   v
+--------------------+---+   +-----------+-------+   +-------+----------------------+
|   GIT INGESTION        |   | TEMPORAL RAG      |   |  OLLAMA LOCAL LLM ENGINE     |
| - GitPython Extractor  |   | - Intent Router   |   | - qwen2.5-coder / deepseek   |
| - ThreadPool Diff      |   | - Positional Index|   | - 60m VRAM Keep-Alive        |
| - Overview Context     |   | - Cosine Re-Ranker|   | - HTTP Async Connection Pool |
+--------------------+---+   +-----------+-------+   +------------------------------+
                     |                   |
                     v                   v
+--------------------+-------------------+------------------------------------------+
|                            CHROMADB VECTOR STORE                                  |
|  Collection: code_archaeologist_commits (384-d dense vectors, HNSW Cosine Index) |
+-----------------------------------------------------------------------------------+
```

---

## 🛠️ Technology Stack

| Domain                | Technology                     | Description                                                          |
| :-------------------- | :----------------------------- | :------------------------------------------------------------------- |
| **Frontend**          | React 18, Vite 6, Tailwind CSS | High-performance SPA with lazy-loaded Recharts and Lucide icons.     |
| **Backend API**       | Python 3.10+, FastAPI, Uvicorn | Asynchronous ASGI server with Pydantic validation and SSE streaming. |
| **AI / Embeddings**   | SentenceTransformers, Ollama   | Local dense 384-d `all-MiniLM-L6-v2` embeddings and local GPU LLM.   |
| **Vector Database**   | ChromaDB (v0.4+)               | Persistent in-process vector database with metadata filtering.       |
| **Repository Mining** | GitPython, ThreadPoolExecutor  | Multithreaded Git commit parsing and AST diff summary extraction.    |

---

## 📁 Project Structure

```text
code-archaeologist/
├── backend/
│   ├── main.py                     # FastAPI ASGI application & lifespan handler
│   ├── requirements.txt            # Python dependencies
│   ├── app/
│   │   ├── api/routes/             # REST API endpoints
│   │   │   ├── repo.py             # Ingestion & Intelligence routes
│   │   │   ├── chat.py             # Q&A & Causal Reasoning streaming routes
│   │   │   ├── evolution.py        # Timeline narrative routes
│   │   │   └── analysis.py         # Bug Origin & Debug Telemetry routes
│   │   ├── core/                   # Configuration & Logging setup
│   │   ├── ingestion/              # Git mining & overview context parser
│   │   ├── models/                 # Pydantic data schemas
│   │   ├── reasoning/              # Intelligence engine, Scorer & Ollama client
│   │   └── temporal_rag/           # ChromaDB client & Temporal Retriever
│   ├── scripts/                    # Diagnostic & Evaluation benchmark scripts
│   │   ├── evaluate_retrieval.py   # Grounding quality evaluator (10 queries)
│   │   └── run_full_validation.py  # End-to-end performance profiler
│   └── tests/                      # Automated unittest suite
├── frontend/
│   ├── package.json                # Node dependencies & scripts
│   ├── vite.config.js              # Vite configuration & vendor chunk splitting
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

This project is developed for educational, academic research, and software engineering evaluation purposes.

---

## 👤 Author

- **Name**: Adithyan S
- **Degree**: B.Tech Artificial Intelligence & Data Science
- **Project**: Code Archaeologist — Temporal RAG Software Evolution Intelligence Platform
