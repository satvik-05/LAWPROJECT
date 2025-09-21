## IPC Legal Assistant (Informational Chatbot)

An ML + LLM chatbot that analyzes user-described incidents, retrieves relevant Indian Penal Code (IPC) sections using embeddings + RAG, and explains them in simple language with next-step guidance.

### Features
- NLP fact extraction with spaCy
- Embeddings + RAG over IPC sections (Chroma)
- LLM explanations (OpenAI)
- FastAPI backend + Streamlit UI
- Clear legal disclaimer

### Quickstart
1. Python 3.10+
2. Create env and install:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env # add your OpenAI key
```
3. Ingest IPC data (sample included):
```bash
python scripts/ingest_ipc.py
```
4. Run backend:
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
5. Run UI:
```bash
streamlit run frontend/app.py
```

### Disclaimer
This tool is for informational purposes only and is not legal advice. It does not create a lawyer-client relationship. For legal decisions, consult a qualified advocate.

### Project Structure
- `backend/` FastAPI app and RAG services
- `frontend/` Streamlit UI
- `scripts/` data ingestion
- `data/` IPC dataset

### Configuration
Configure `.env` for keys and models. Default vector store: `vectorstore/`. 