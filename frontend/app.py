import os
import streamlit as st
import requests
from dotenv import load_dotenv
import subprocess
import time
import atexit
import sys

load_dotenv()

# For Hugging Face Spaces, the backend runs on the same host
# Check if we're running on HF Spaces
IS_HF_SPACE = os.getenv("SPACE_ID") is not None

if IS_HF_SPACE:
    # On HF Spaces, backend runs on port 8000
    API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
    
    # Start backend only once using a lock file
    LOCK_FILE = "/tmp/backend_started.lock"
    
    if not os.path.exists(LOCK_FILE):
        try:
            # Check if backend is already running
            requests.get(f"{API_BASE}/health", timeout=2)
            print("✅ Backend already running")
            open(LOCK_FILE, 'w').close()
        except:
            # Backend not running, start it (only first process)
            try:
                # Create lock file atomically
                fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                
                # Pre-initialize RAG service to build vectorstore
                print("🔧 Pre-initializing RAG service...")
                result = subprocess.run([sys.executable, "pre_init.py"], 
                                      capture_output=True, text=True, timeout=180)
                if result.returncode == 0:
                    print(result.stdout)
                else:
                    print(f"⚠️ Pre-initialization failed: {result.stderr}")
                
                print("🔧 Starting FastAPI backend...")
                backend_process = subprocess.Popen([
                    "uvicorn", "backend.app.main:app",
                    "--host", "0.0.0.0",
                    "--port", "8000"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Wait for it to start
                time.sleep(10)
                print("✅ Backend started")
            except FileExistsError:
                # Another process is already starting the backend
                print("⏳ Waiting for backend to start...")
                time.sleep(25)
            except subprocess.TimeoutExpired:
                print("⚠️ Pre-initialization timed out, starting backend anyway...")
            except Exception as e:
                print(f"⚠️ Error during initialization: {e}")
else:
    API_BASE = os.getenv("API_BASE", "http://localhost:8000")

st.set_page_config(page_title="IPC Legal Assistant", page_icon="⚖️", layout="centered")

# Custom CSS for better appearance
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        padding: 1rem 0;
    }
    .disclaimer {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">⚖️ IPC Legal Assistant</h1>', unsafe_allow_html=True)

st.markdown(
    '<div class="disclaimer">'
    '<strong>⚠️ Important Disclaimer:</strong><br>'
    'This chatbot provides general information based on the Indian Penal Code (IPC). '
    'It is for <strong>informational purposes only</strong> and is <strong>not legal advice</strong>. '
    'This tool does not establish a lawyer-client relationship. '
    'For legal decisions, please consult a qualified advocate.'
    '</div>',
    unsafe_allow_html=True
)

# Instructions
with st.expander("ℹ️ How to use this assistant"):
    st.markdown("""
    1. **Describe your situation** in the text box below
    2. Be as detailed as possible (who, what, when, where)
    3. Click the **Ask** button
    4. The assistant will:
        - Analyze your description
        - Retrieve relevant IPC sections
        - Provide an explanation in simple language
        - Suggest possible next steps
    
    **Example:** "Someone snatched my phone on the street last night when I was walking home."
    """)

# Main input
user_input = st.text_area(
    "Describe your situation",
    height=150,
    placeholder="Example: Someone snatched my phone on the street last night...",
    help="Provide as much detail as possible about the incident"
)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    ask_button = st.button("🔍 Ask the Assistant", use_container_width=True)

if ask_button:
    if not user_input.strip():
        st.warning("⚠️ Please describe your situation before asking.")
    else:
        with st.spinner("🔄 Analyzing and retrieving relevant IPC sections..."):
            try:
                resp = requests.post(
                    f"{API_BASE}/api/chat",
                    json={"message": user_input},
                    timeout=180  # Increased to 180 seconds (3 minutes)
                )
                resp.raise_for_status()
                data = resp.json()
                
                # Display response
                st.success("✅ Analysis Complete")
                st.markdown("### 📝 Response")
                st.markdown(data.get("reply", ""))
                
                # Display sources
                sources = data.get("source_sections", [])
                if sources:
                    with st.expander("📚 View Source IPC Sections", expanded=True):
                        for idx, s in enumerate(sources, 1):
                            st.markdown(f"{idx}. {s}")
                            
            except requests.exceptions.Timeout:
                st.error("⏱️ Request timed out. Please try again.")
            except requests.exceptions.ConnectionError:
                st.error("🔌 Unable to connect to the backend service. Please try again in a moment.")
            except requests.exceptions.HTTPError as e:
                st.error(f"❌ HTTP Error: {e.response.status_code}")
                if e.response.status_code == 500:
                    st.info("The server encountered an error. This might be due to API configuration. Please check the Space settings.")
            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <small>
    Made with ❤️ for educational purposes • 
    <a href="https://github.com" target="_blank">GitHub</a>
    </small>
</div>
""", unsafe_allow_html=True)

# Show API connection status in sidebar
with st.sidebar:
    st.markdown("### 🔧 System Status")
    try:
        health_resp = requests.get(f"{API_BASE}/health", timeout=5)
        if health_resp.status_code == 200:
            st.success("✅ Backend Connected")
        else:
            st.warning("⚠️ Backend Issue")
    except:
        st.error("❌ Backend Offline")
    
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown("""
    This assistant uses:
    - **NLP** for fact extraction
    - **RAG** for IPC section retrieval
    - **LLM** for explanations
    """)
    
    # Show if API key is configured
    if os.getenv("OPENAI_API_KEY"):
        st.info("🔑 Using OpenAI")
    elif os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        st.info("🔑 Using Google Gemini")
    else:
        st.warning("⚠️ No API key configured. Please add OPENAI_API_KEY or GEMINI_API_KEY in Space settings.") 