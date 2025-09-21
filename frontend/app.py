import os
import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

st.set_page_config(page_title="IPC Legal Assistant", page_icon="⚖️")

st.title("⚖️ IPC Legal Assistant")

st.markdown(
	"This chatbot provides general information based on the Indian Penal Code (IPC).\n\n"
	"It is for informational purposes only and is not legal advice."
)

user_input = st.text_area("Describe your situation", height=150, placeholder="e.g., Someone snatched my phone on the street last night...")

if st.button("Ask"):
	if not user_input.strip():
		st.warning("Please describe your situation.")
	else:
		with st.spinner("Analyzing and retrieving relevant IPC sections..."):
			try:
				resp = requests.post(f"{API_BASE}/api/chat", json={"message": user_input}, timeout=60)
				resp.raise_for_status()
				data = resp.json()
				st.subheader("Response")
				st.write(data.get("reply", ""))
				sources = data.get("source_sections", [])
				if sources:
					st.markdown("**Sources (IPC sections):**")
					for s in sources:
						st.write(f"- {s}")
			except Exception as e:
				st.error(f"Error: {e}")

st.divider()

st.caption("This tool does not establish a lawyer-client relationship. Consult a qualified advocate for legal advice.") 