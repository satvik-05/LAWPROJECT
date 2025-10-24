from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logging
from backend.services.rag_service import RAGService

class ChatRequest(BaseModel):
	message: str

class ChatResponse(BaseModel):
	reply: str
	source_sections: list[str]

app = FastAPI(title="IPC Legal Assistant", version="0.1.0")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ipc-assistant")

# Initialize RAG service at module level
logger.info("Initializing RAG service...")
rag_service = RAGService()
logger.info("RAG service ready!")

@app.on_event("startup")
async def startup_event():
	logger.info("Backend startup complete - ready to serve requests")

@app.get("/health")
async def health():
	return {"status": "ok", "rag_initialized": rag_service is not None}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
	try:
		reply, source_sections = rag_service.answer_query(req.message)
		return ChatResponse(reply=reply, source_sections=source_sections)
	except Exception as e:
		logger.exception("Chat generation failed: %s", e)
		fallback = (
			"I'm unable to generate a full explanation right now due to a local model error. "
			"Here are likely relevant IPC sections based on retrieval."
		)
		try:
			source_labels, _ = rag_service._retrieve_sections(req.message)
			return ChatResponse(reply=fallback, source_sections=source_labels)
		except Exception as inner:
			logger.exception("Retrieval failed: %s", inner)
			return ChatResponse(reply=str(e), source_sections=[]) 