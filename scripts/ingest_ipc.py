import os
import re
import pandas as pd
from dotenv import load_dotenv
import shutil
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

DATA_PATH = os.getenv("IPC_DATA_PATH", "data/FIR_DATASET.csv")
VECTORSTORE_DIR = os.getenv("VECTORSTORE_DIR", "vectorstore")
REBUILD_VECTORSTORE = os.getenv("REBUILD_VECTORSTORE", "").lower() in ("1", "true", "yes")
EMBED_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
LOCAL_EMBED_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if GEMINI_API_KEY and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/text-embedding-004")
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "").lower() in ("1", "true", "yes")
USE_GEMINI_LLM = os.getenv("USE_GEMINI_LLM", "").lower() in ("1", "true", "yes")


def get_embeddings():
    use_local = os.getenv("USE_LOCAL_EMBEDDINGS", "").lower() in ("1", "true", "yes")
    if not use_local and not USE_LOCAL_LLM:
        # Prefer OpenAI unless Gemini is explicitly selected
        if os.getenv("OPENAI_API_KEY") and not USE_GEMINI_LLM:
            return OpenAIEmbeddings(model=EMBED_MODEL)
        # Use Gemini embeddings if key available
        if GEMINI_API_KEY:
            return GoogleGenerativeAIEmbeddings(model=GEMINI_EMBED_MODEL)
    return SentenceTransformerEmbeddings(model_name=LOCAL_EMBED_MODEL)


def normalize_rows(df: pd.DataFrame) -> tuple[list[str], list[dict]]:
    texts: list[str] = []
    metadatas: list[dict] = []
    cols = {c.lower(): c for c in df.columns}
    def _safe(s):
        if s is None:
            return ""
        try:
            if pd.isna(s):
                return ""
        except Exception:
            pass
        ss = str(s).strip()
        return "" if ss.lower() == "nan" else ss
    # Case A: canonical IPC schema
    if all(k in cols for k in ["section_number", "title", "text"]):
        for _, row in df.iterrows():
            sec = _safe(row[cols['section_number']])
            title = _safe(row[cols['title']]) or f"IPC Section {sec}"
            text = _safe(row[cols['text']])
            content = f"Section {sec}: {title}\n{text}"
            texts.append(content)
            metadatas.append({
                "section_number": str(sec),
                "title": title,
            })
        return texts, metadatas
    # Case B: FIR_DATASET schema: URL, Description, Offense, Punishment, Cognizable, Bailable, Court
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


def main() -> None:
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    texts, metadatas = normalize_rows(df)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=150)
    docs = text_splitter.create_documents(texts, metadatas=metadatas)
    embeddings = get_embeddings()
    # Optionally wipe existing vectorstore for a clean rebuild
    if REBUILD_VECTORSTORE and os.path.isdir(VECTORSTORE_DIR):
        shutil.rmtree(VECTORSTORE_DIR, ignore_errors=True)
    vs = Chroma.from_documents(docs, embeddings, persist_directory=VECTORSTORE_DIR)
    # Note: persist() is deprecated in newer Chroma versions, data is auto-persisted
    print(f"Ingestion complete. Vector store at: {VECTORSTORE_DIR}")


if __name__ == "__main__":
    main()