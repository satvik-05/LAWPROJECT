#!/usr/bin/env python3
"""
Pre-initialize the RAG service to build vectorstore before serving requests.
This runs once during HF Spaces startup to avoid timeout on first request.
"""
import os
import sys

# Add the project root to Python path
sys.path.insert(0, '/home/user/app')

print("🔧 Pre-initializing RAG service...")

try:
    from backend.services.rag_service import RAGService
    
    # This will build the vectorstore if it doesn't exist
    print("📊 Loading/building vectorstore...")
    rag = RAGService()
    print("✅ RAG service initialized successfully!")
    print(f"   - Vectorstore ready at: {os.getenv('VECTORSTORE_DIR', 'vectorstore')}")
    
except Exception as e:
    print(f"❌ Failed to initialize RAG service: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
