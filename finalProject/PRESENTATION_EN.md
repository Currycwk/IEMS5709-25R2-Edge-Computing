# Slide 1 - Title

## Edge-Deployable Local RAG System with Qwen3 and BGE-M3

**Course:** IEMS5709A Edge Computing  
**Project Type:** Final Project  
**Team:** [Add team member names]  
**Date:** April 2026

---

# Slide 2 - Motivation

## Why This Project?

- Large language models can generate fluent answers, but they may hallucinate.
- Many useful documents are private, local, or domain-specific.
- Cloud-based AI services may introduce privacy, latency, and cost concerns.
- In edge computing scenarios, a local AI pipeline is more attractive.

### Our Goal

Build a local RAG system that can:

- retrieve facts from a local knowledge base,
- generate grounded answers,
- run on an edge-oriented setup,
- and provide source evidence for every answer.

---

# Slide 3 - Project Objective

## Project Objective

We designed and implemented a **containerized local Retrieval-Augmented Generation system** with:

- a web-based frontend,
- a FastAPI backend,
- a local vector retrieval pipeline,
- and a Qwen3 model served through vLLM.

### Expected Outcomes

- local document ingestion,
- index construction,
- question answering with retrieved context,
- source traceability,
- and support for both local and API-based model backends.

---

# Slide 4 - High-Level Architecture

## System Architecture

### Main Components

- **Frontend**
  - user interaction
  - status check
  - question submission
  - answer and source display

- **Backend**
  - document loading
  - chunking
  - embedding
  - retrieval
  - prompt construction
  - LLM invocation

- **Model Service**
  - local Qwen3 through vLLM
  - optional API-based backend

- **Storage**
  - local knowledge documents
  - local vector index

---

# Slide 5 - End-to-End Workflow

## End-to-End Workflow

1. User uploads or selects documents.
2. Backend loads the documents from the knowledge base.
3. Documents are split into chunks.
4. Chunks are embedded and stored in a vector database.
5. User asks a question.
6. Backend retrieves the most relevant chunks.
7. Retrieved context is passed to Qwen3.
8. The system streams the answer back to the frontend.
9. Supporting sources are displayed for verification.

---

# Slide 6 - Core Technologies

## Core Technologies

- **Frontend:** HTML, CSS, Vue 3, JavaScript
- **Backend:** FastAPI, Python, httpx
- **LLM:** Qwen3-4B
- **Serving:** vLLM (OpenAI-compatible API)
- **Embedding Target:** BGE-M3
- **Vector Retrieval:** local simple vector store / optional FAISS
- **Deployment:** Docker / Docker Compose

### Design Principle

Modular architecture so each stage can be replaced or upgraded independently.

---

# Slide 7 - Implemented Features

## Implemented Features

### Knowledge Base Features

- upload knowledge files
- delete knowledge files
- restrict allowed file types (`.txt`, `.md`, `.pdf`)
- rebuild index from local knowledge base

### QA Features

- streaming answer generation with SSE
- separate display of think content and final answer
- source card display with retrieval evidence
- configurable Top-K retrieval

### External Code Analysis Features

- upload external code projects as ZIP
- build project-specific index
- ask questions about uploaded codebases
- delete uploaded external projects

---

# Slide 8 - Frontend Highlights

## Frontend Highlights

- redesigned Vue-based interface
- fixed-height answer window with internal scrolling
- source panel with scrollable layout
- better input styling for selectors and upload controls
- backend switching support:
  - **Local model backend**
  - **API model backend**

### User Experience Improvements

- clear system status display
- visible retrieval sources
- better handling of long outputs
- more manageable knowledge base and project operations

---

# Slide 9 - Backend Highlights

## Backend Highlights

- unified API for status, indexing, document browsing, and chat
- support for two corpora:
  - `knowledge`
  - `external_code`
- support for source-aware retrieval
- support for streaming response generation
- support for document management and project management

### Backend API Examples

- `GET /api/status`
- `POST /api/index`
- `POST /api/chat`
- `POST /api/knowledge/upload`
- `DELETE /api/knowledge/document`
- `POST /api/code/upload`
- `DELETE /api/code/external/{project_name}`

---

# Slide 10 - Demo Scenarios

## Demo Scenarios

### Scenario 1 - Knowledge Base QA

- upload a local document
- build the index
- ask a question
- observe grounded answer with sources

### Scenario 2 - External Code Analysis

- upload a ZIP code project
- build the project index
- ask architecture or module questions
- inspect supporting code snippets

### Scenario 3 - Backend Switching

- switch between local backend and API backend from the frontend
- compare availability and model behavior

---

# Slide 11 - Challenges We Encountered

## Challenges We Encountered

- local model context/window limitations
- output truncation when prompt + retrieval context became too large
- reasoning / thinking tokens consuming output budget
- stale model services occupying local ports
- GPU memory limitations when starting vLLM on Jetson-oriented environment
- browser cache issues when updating frontend resources

### What We Did

- added clearer backend switching
- improved streaming error handling
- improved UI feedback
- investigated local vLLM startup chain and model serving behavior

---

# Slide 12 - Project Value

## Why This Project Matters

- demonstrates how RAG can be deployed in an edge-style local environment
- improves privacy by keeping documents local
- increases answer reliability through retrieval grounding
- provides explainability by showing supporting sources
- supports both knowledge QA and external code understanding

This makes the project suitable as both:

- a practical edge AI prototype,
- and a teaching/demo system for local LLM applications.

---

# Slide 13 - Limitations

## Current Limitations

- local model context behavior still depends on runtime serving configuration
- retrieval quality depends on embedding quality and chunking strategy
- local deployment may be constrained by GPU memory
- long-context handling on local model is still less stable than cloud API mode
- current interface is functional, but not yet polished as a production dashboard

---

# Slide 14 - Future Work

## Future Work

- improve local long-context support
- optimize chunking and reranking strategy
- integrate stronger local embedding inference for BGE-M3
- support richer file management and metadata filtering
- add evaluation metrics for retrieval quality and answer grounding
- add role-based or multi-user support
- further improve deployment robustness on edge hardware

---

# Slide 15 - Conclusion

## Conclusion

We built a **local RAG system for edge-oriented deployment** that combines:

- local or API-based LLM access,
- document retrieval,
- source-grounded answering,
- and a usable web interface.

The project shows that:

- local AI question answering is feasible,
- retrieval improves factual grounding,
- and modular edge AI systems can be built with manageable components.

### Thank You

Questions and discussion are welcome.

---

# Optional Appendix - Team Contribution

## Team Contribution

- **Member A:** frontend design and interaction
- **Member B:** backend API and RAG pipeline
- **Member C:** model deployment and local serving
- **Member D:** testing, debugging, and documentation

> Replace with your actual division of work.

---

# Optional Appendix - AI Tool Usage Disclosure

## AI Tool Usage Disclosure

This project used AI tools for:

- code drafting,
- debugging assistance,
- architecture refinement,
- and documentation writing support.

### Tools Used

- Cursor
- GPT-based coding assistant
- Qwen-related model serving tools

> Replace with the exact tools and specific usage required by your course policy.
