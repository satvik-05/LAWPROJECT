---
title: IPC Legal Assistant
emoji: ⚖️
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: 1.38.0
app_file: frontend/app.py
pinned: false
license: mit
startup_duration_timeout: 5m
---

## IPC Legal Assistant (Informational Chatbot)

An ML + LLM chatbot that analyzes user-described incidents, retrieves relevant Indian Penal Code (IPC) sections using embeddings + RAG, and explains them in simple language with next-step guidance.

### Features

- NLP fact extraction with spaCy
- Embeddings + RAG over IPC sections (Chroma)
- LLM explanations (OpenAI/Gemini)
- FastAPI backend + Streamlit UI
- Clear legal disclaimer

### Deployment on Hugging Face Spaces

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions on deploying to Hugging Face Spaces.

**Quick Setup:**

1. Create a new Space on Hugging Face with Streamlit SDK
2. Upload this repository
3. Add your `OPENAI_API_KEY` or `GEMINI_API_KEY` in Space settings
4. Wait for the build to complete

### Local Development

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

- `backend/` - FastAPI app and RAG services
- `frontend/` - Streamlit UI
- `scripts/` - Data ingestion scripts
- `data/` - IPC dataset
- `vectorstore/` - Vector database (auto-generated)

### Configuration

Configure environment variables for API keys and models:

**Required (choose one):**

- `OPENAI_API_KEY` - OpenAI API key
- `GEMINI_API_KEY` or `GOOGLE_API_KEY` - Google Gemini API key

**Optional:**

- `USE_GEMINI_LLM=true` - Use Gemini instead of OpenAI
- `USE_LOCAL_EMBEDDINGS=true` - Use local embeddings
- `OPENAI_MODEL=gpt-4o-mini` - OpenAI model to use
- `GEMINI_MODEL=gemini-1.5-flash` - Gemini model to use

Default vector store: `vectorstore/`
