import os
import re
import requests
import pandas as pd
import spacy
from dotenv import load_dotenv
from typing import List, Tuple

from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from openai import OpenAI
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

load_dotenv()

VECTORSTORE_DIR = os.getenv("VECTORSTORE_DIR", "vectorstore")
DATA_PATH = os.getenv("IPC_DATA_PATH", "data/FIR_DATASET.csv")
CHAT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
EMBED_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
LOCAL_EMBED_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "").lower() in ("1", "true", "yes")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Gemini configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
# Propagate to GOOGLE_API_KEY for LangChain provider compatibility
if GEMINI_API_KEY and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/embedding-001")
USE_GEMINI_LLM = os.getenv("USE_GEMINI_LLM", "").lower() in ("1", "true", "yes")


def get_embeddings():
	use_local = os.getenv("USE_LOCAL_EMBEDDINGS", "").lower() in ("1", "true", "yes")
	if not use_local and not USE_LOCAL_LLM:
		# Prefer OpenAI unless Gemini is explicitly selected
		if os.getenv("OPENAI_API_KEY") and not USE_GEMINI_LLM:
			return OpenAIEmbeddings(model=EMBED_MODEL)
		# Use Gemini embeddings if key is available or explicitly selected
		if GEMINI_API_KEY:
			return GoogleGenerativeAIEmbeddings(model=GEMINI_EMBED_MODEL)
	# Fallback to local sentence-transformers
	return SentenceTransformerEmbeddings(model_name=LOCAL_EMBED_MODEL)


class RAGService:
	def __init__(self) -> None:
		self.client = None if USE_LOCAL_LLM else (OpenAI() if os.getenv("OPENAI_API_KEY") else None)
		self.gemini_chat = None
		if not USE_LOCAL_LLM and GEMINI_API_KEY and (USE_GEMINI_LLM or not self.client):
			self.gemini_chat = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=0.2)
		self.embeddings = get_embeddings()
		self.vectorstore = self._load_or_build_vectorstore()
		# Use MMR to diversify results and fetch a few more candidates
		self.retriever = self.vectorstore.as_retriever(
			search_type="mmr",
			search_kwargs={"k": 6, "lambda_mult": 0.5},
		)
		self.nlp = spacy.load("en_core_web_sm")

	def _normalize_rows(self, df: pd.DataFrame) -> tuple[list[str], list[dict]]:
		texts: list[str] = []
		metadatas: list[dict] = []
		cols = {c.lower(): c for c in df.columns}
		def _safe(s):
			# Return empty string for NaN/None, else stripped string
			if s is None:
				return ""
			try:
				if pd.isna(s):
					return ""
			except Exception:
				pass
			ss = str(s).strip()
			return "" if ss.lower() == "nan" else ss
		if all(k in cols for k in ["section_number", "title", "text"]):
			for _, row in df.iterrows():
				content = f"Section {row[cols['section_number']]}: {row[cols['title']]}\n{row[cols['text']]}"
				texts.append(content)
				metadatas.append({
					"section_number": str(row[cols["section_number"]]),
					"title": str(row[cols["title"]]),
				})
			return texts, metadatas
		if all(k in cols for k in ["url", "description"]) and "offense" in cols:
			sec_num_re = re.compile(r"section[-_/](\d+)")
			for _, row in df.iterrows():
				url = _safe(row[cols["url"]])
				desc = _safe(row[cols["description"]])
				offense = _safe(row[cols["offense"]]) if "offense" in cols else ""
				punishment = _safe(row[cols.get("punishment")]) if "punishment" in cols else ""
				cognizable = _safe(row[cols.get("cognizable")]) if "cognizable" in cols else ""
				bailable = _safe(row[cols.get("bailable")]) if "bailable" in cols else ""
				court = _safe(row[cols.get("court")]) if "court" in cols else ""
				m = sec_num_re.search(url.lower())
				section_number = m.group(1) if m else "?"
				title = offense if offense else f"IPC Section {section_number}"
				meta_block = []
				if punishment:
					meta_block.append(f"Punishment: {punishment}")
				if cognizable:
					meta_block.append(f"Cognizable: {cognizable}")
				if bailable:
					meta_block.append(f"Bailable: {bailable}")
				if court:
					meta_block.append(f"Court: {court}")
				meta_text = "\n".join(meta_block)
				content = f"Section {section_number}: {title}\n{desc}\n\n{meta_text}".strip()
				texts.append(content)
				metadatas.append({
					"section_number": str(section_number),
					"title": title,
					"source_url": url,
				})
			return texts, metadatas
		raise ValueError("Unsupported dataset schema. Expected columns for IPC or FIR_DATASET.")

	def _load_or_build_vectorstore(self) -> Chroma:
		if os.path.isdir(VECTORSTORE_DIR) and os.listdir(VECTORSTORE_DIR):
			return Chroma(persist_directory=VECTORSTORE_DIR, embedding_function=self.embeddings)
		if not os.path.exists(DATA_PATH):
			raise FileNotFoundError(f"IPC dataset not found at {DATA_PATH}")
		df = pd.read_csv(DATA_PATH)
		texts, metadatas = self._normalize_rows(df)
		text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=150)
		docs = text_splitter.create_documents(texts, metadatas=metadatas)
		vs = Chroma.from_documents(docs, self.embeddings, persist_directory=VECTORSTORE_DIR)
		return vs

	def _extract_facts(self, query: str) -> dict:
		doc = self.nlp(query)
		entities = [(ent.text, ent.label_) for ent in doc.ents]
		keywords = [token.lemma_ for token in doc if token.is_alpha and not token.is_stop]
		return {"entities": entities, "keywords": keywords[:15]}

	def _retrieve_sections(self, query: str) -> Tuple[List[str], List[str]]:
		# Use the new invoke API (get_relevant_documents is deprecated)
		results = self.retriever.invoke(query)
		source_texts: list[str] = []
		source_labels: list[str] = []
		seen: set[str] = set()

		def build_label(doc) -> str:
			meta = doc.metadata or {}
			sec = str(meta.get("section_number", "")).strip()
			title = (meta.get("title", "") or "").strip()
			text = doc.page_content or ""
			# Try to infer section number from content if missing/unknown
			if not sec or sec == "?":
				m = re.search(r"Section\s+(\d+)", text[:300], flags=re.IGNORECASE)
				if not m:
					m = re.search(r"IPC\s*(\d+)", text[:300], flags=re.IGNORECASE)
				sec = m.group(1) if m else ""
			# Try to infer a cleaner title from content if title is empty or generic
			if not title or title.lower().startswith("ipc section"):
				m2 = re.search(r"Section\s+\d+\s*:\s*(.+)", text.splitlines()[0] if text else "")
				if m2:
					title = m2.group(1).strip()
			# Build label components, avoid '?' artifacts
			parts = []
			if sec:
				parts.append(f"IPC {sec}")
			if title:
				parts.append(title)
			label = " - ".join(parts) if parts else (text[:50] + ("..." if len(text) > 50 else ""))
			return label

		for doc in results:
			label = build_label(doc)
			if label in seen:
				continue
			seen.add(label)
			source_labels.append(label)
			source_texts.append(doc.page_content)
		return source_labels, source_texts

	def _build_prompt(self, query: str, facts: dict, sources: List[str]) -> str:
		joined_sources = "\n\n".join([f"Source {i+1}:\n" + s for i, s in enumerate(sources)])
		return (
			"You are a legal assistant for Indian Penal Code (IPC). "
			"Answer ONLY using the provided sources. "
			"Explain in simple terms, outline relevant sections, and suggest next steps (e.g., FIR).\n\n"
			f"User query:\n{query}\n\n"
			f"Extracted facts (no need to repeat verbatim): {facts}\n\n"
			f"IPC sources:\n{joined_sources}\n\n"
			"Guidelines: Be accurate, avoid speculation, and include a disclaimer: "
			"'This is informational, not legal advice.'"
		)

	def _fallback_explanation(self, query: str, facts: dict, source_labels: List[str], source_texts: List[str]) -> str:
		"""Create a plain, non-LLM explanation that is still useful to the user.

		This stitches together the retrieved sections, highlights entities/keywords, and adds
		a clear disclaimer. This ensures the app works even without OpenAI/Ollama.
		"""
		entities = ", ".join([f"{t} ({l})" for t, l in facts.get("entities", [])]) or "—"
		keywords = ", ".join(facts.get("keywords", [])[:10]) or "—"
		sec_lines = "\n".join([f"- {lbl}" for lbl in source_labels]) if source_labels else "- (no sections found)"
		guidance = (
			"Based on the retrieved IPC sections above, consider filing an FIR at your local police station "
			"if the incident constitutes a cognizable offence. Collect any evidence (photos, receipts, witness details) and "
			"note the date, time, and place of occurrence."
		)
		disclaimer = (
			"\n\nDisclaimer: This is for informational purposes only and is not legal advice. "
			"Please consult a qualified advocate for advice on your specific situation."
		)
		intro = (
			"Here is a brief analysis synthesized without a language model (offline mode):\n\n"
			f"Your description: {query}\n"
			f"Detected entities: {entities}\n"
			f"Keywords: {keywords}\n\n"
			"Likely relevant IPC sections:\n"
		)
		return intro + sec_lines + "\n\n" + guidance + disclaimer

	def _ollama_chat(self, prompt: str) -> str:
		# Try the chat endpoint first
		url = f"{OLLAMA_HOST}/api/chat"
		payload = {
			"model": OLLAMA_MODEL,
			"messages": [
				{"role": "system", "content": "You are a helpful legal assistant for IPC queries."},
				{"role": "user", "content": prompt},
			],
			"options": {"temperature": 0.2},
			"stream": False,
		}
		try:
			resp = requests.post(url, json=payload, timeout=180)
			resp.raise_for_status()
			data = resp.json()
			if isinstance(data, dict) and "message" in data:
				return data["message"].get("content", "")
			if isinstance(data, dict) and "response" in data:
				return data.get("response", "")
			return str(data)
		except Exception:
			# Fallback to generate endpoint if chat fails
			gen_url = f"{OLLAMA_HOST}/api/generate"
			gen_payload = {
				"model": OLLAMA_MODEL,
				"prompt": prompt,
				"options": {"temperature": 0.2},
				"stream": False,
			}
			resp = requests.post(gen_url, json=gen_payload, timeout=180)
			resp.raise_for_status()
			data = resp.json()
			# /api/generate returns {"response": "...", ...}
			return data.get("response", str(data))

	def answer_query(self, query: str) -> Tuple[str, List[str]]:
		facts = self._extract_facts(query)
		source_labels, source_texts = self._retrieve_sections(query)
		prompt = self._build_prompt(query, facts, source_texts)
		# Try OpenAI first if configured and Gemini not explicitly requested
		if self.client and not USE_LOCAL_LLM and not USE_GEMINI_LLM:
			try:
				completion = self.client.chat.completions.create(
					model=CHAT_MODEL,
					messages=[
						{"role": "system", "content": "You are a helpful legal assistant for IPC queries."},
						{"role": "user", "content": prompt},
					],
					temperature=0.2,
					timeout=120,  # Increased to 120 seconds (2 minutes)
				)
				reply = completion.choices[0].message.content
				return reply, source_labels
			except Exception as e:
				# Log and continue to other fallbacks
				print(f"OpenAI failed: {e}")
				pass
		# Try Gemini if configured
		if self.gemini_chat and not USE_LOCAL_LLM:
			try:
				# Use invoke with timeout handling
				import asyncio
				from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
				
				def _gemini_call():
					result = self.gemini_chat.invoke(prompt)
					return getattr(result, "content", str(result))
				
				with ThreadPoolExecutor() as executor:
					future = executor.submit(_gemini_call)
					reply = future.result(timeout=120)  # Increased to 120 seconds (2 minutes)
					return reply, source_labels
			except FuturesTimeoutError:
				print("Gemini request timed out")
				pass
			except Exception as e:
				# Continue to other fallbacks
				print(f"Gemini failed: {e}")
				pass
		# Else try local LLM via Ollama
		if USE_LOCAL_LLM:
			try:
				reply = self._ollama_chat(prompt)
				return reply, source_labels
			except Exception:
				return self._fallback_explanation(query, facts, source_labels, source_texts), source_labels
		# Neither OpenAI nor local LLM configured - use fallback
		return self._fallback_explanation(query, facts, source_labels, source_texts), source_labels