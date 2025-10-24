# HF Spaces Deployment - Storage Optimization

## Problem Fixed

**Error**: `Workload evicted, storage limit exceeded (50G)`

## Root Cause

Multiple processes were downloading models simultaneously:

- spaCy model (12.8 MB × 3 = ~40 MB)
- sentence-transformers model (90.9 MB × 3 = ~270 MB)
- ChromaDB creating multiple databases
- Unnecessary dependencies (llama-index, faiss, gradio, numpy)

## Solutions Applied

### 1. **Reduced Dependencies** (requirements.txt)

Removed:

- `llama-index==0.11.15` (heavy, unused)
- `faiss-cpu==1.8.0.post1` (large, not needed)
- `gradio==4.44.0` (unused UI framework)
- `numpy==1.26.4` (comes with pandas)

**Savings**: ~5-10 GB

### 2. **Prevented Duplicate Downloads** (frontend/app.py)

- Added `st.session_state` check to start backend only once
- Changed port from 7860 to 8000 (standard)
- Increased backend startup wait time to 15 seconds
- Removed spaCy download from frontend (handled by requirements)

### 3. **Increased Startup Timeout** (README.md)

- Added `startup_duration_timeout: 5m` to HF frontmatter
- Gives more time for vectorstore creation on first run

### 4. **Created .slugignore**

Excludes build artifacts and documentation from deployment

### 5. **Environment Variables Set**

- `USE_LOCAL_EMBEDDINGS=true` - Uses sentence-transformers instead of Gemini API

## Expected Behavior

### First Startup (2-5 minutes)

1. Install Python dependencies
2. Download spaCy model `en_core_web_sm` (12.8 MB)
3. Download sentence-transformers model `all-MiniLM-L6-v2` (90.9 MB)
4. Load IPC dataset (FIR_DATASET.csv)
5. Create ChromaDB vectorstore (~100-200 MB)
6. Start FastAPI backend
7. Start Streamlit frontend

### Subsequent Restarts (<1 minute)

- Models cached
- Vectorstore persisted
- Quick startup

## Storage Breakdown

| Component | Size | Notes |
|-----------|------|-------|
| Dependencies | ~2 GB | Optimized from ~7 GB |
| spaCy model | 13 MB | Cached after first download |
| Sentence-transformers | 91 MB | Cached after first download |
| ChromaDB vectorstore | ~200 MB | Built once, persisted |
| Application code | <5 MB | Minimal |
| **Total** | **~2.3 GB** | Well under 50 GB limit |

## Monitoring

Check Space status at:
<https://huggingface.co/spaces/satvik-05/ipc-legal-assistant>

### Logs to Watch For

✅ **Success indicators**:

```
📦 Downloading spaCy model...
✅ spaCy model downloaded
🔧 Starting FastAPI backend...
✅ Backend started
INFO:sentence_transformers.SentenceTransformer:Load pretrained SentenceTransformer
INFO:chromadb.telemetry.product.posthog:Anonymized telemetry enabled
```

❌ **Failure indicators**:

```
Workload evicted, storage limit exceeded
sqlite3.OperationalError: table embeddings_queue already exists
AttributeError: 'Chroma' object has no attribute 'persist'
```

## Next Steps

1. **Wait 3-5 minutes** for Space to rebuild
2. **Check logs** for successful model downloads
3. **Verify "✅ Backend Connected"** in sidebar
4. **Test with query**: "Someone snatched my phone. What can I do legally?"

## Adding API Keys (Optional)

For LLM functionality, add ONE of these secrets in Space settings:

**Option A: Gemini (Free)**

```
GEMINI_API_KEY = your-new-gemini-key
```

**Option B: OpenAI**

```
OPENAI_API_KEY = your-openai-key
```

Without an API key, embeddings will work but queries won't generate answers.

## Rollback Plan

If issues persist, revert to simpler deployment:

```bash
git revert HEAD
git push space main
```

## Contact

Space URL: <https://huggingface.co/spaces/satvik-05/ipc-legal-assistant>
Settings: <https://huggingface.co/spaces/satvik-05/ipc-legal-assistant/settings>
