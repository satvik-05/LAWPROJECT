# Hugging Face Spaces Deployment Instructions

## Your project is ready for deployment! 🚀

### Files prepared for upload

- ✅ README.md (with HF Spaces frontmatter)
- ✅ requirements.txt
- ✅ backend/ (FastAPI application)
- ✅ frontend/ (Streamlit app)
- ✅ scripts/ (data ingestion)
- ✅ data/ (IPC dataset)
- ✅ .streamlit/ (configuration)
- ✅ start.sh (startup script)
- ✅ .huggingface/ (pre-start hooks)

### Deployment Steps

1. **Go to Hugging Face Spaces**
   - Visit: <https://huggingface.co/new-space>
   - Space name: Choose any name (e.g., `ipc-legal-assistant`)
   - SDK: Select **Streamlit**
   - Hardware: CPU basic (free)
   - Click **Create Space**

2. **Upload via Git**

   ```bash
   # Initialize git (if not already done)
   git init
   git add .
   git commit -m "Initial commit: IPC Legal Assistant"
   
   # Add your HF Space as remote
   git remote add space https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
   
   # Push to HF Space
   git push --force space main
   ```

   OR use the web interface to upload files.

3. **Add Secrets in Space Settings**
   - Go to your Space → Settings → Variables and secrets
   - Add these secrets:

     ```
     Name: GEMINI_API_KEY
     Value: AIzaSyCXvGCe8bntI3Z3n7UKwTc8qd6aHru2xts
     
     Name: USE_GEMINI_LLM
     Value: true
     
     Name: GEMINI_MODEL
     Value: gemini-1.5-flash
     ```

4. **Wait for Build**
   - Build takes ~5-10 minutes
   - Check Logs tab for progress
   - App will auto-start when ready

5. **Test Your App**
   - Try query: "Someone snatched my phone. What legal action can I take?"
   - Check sidebar for "Backend Connected" status

## ⚠️ IMPORTANT SECURITY NOTE

Your current API key `AIzaSyCXvGCe8bntI3Z3n7UKwTc8qd6aHru2xts` was shared in our chat.
Please:

1. Go to <https://makersuite.google.com/app/apikey>
2. Revoke the current key
3. Generate a new key
4. Use the NEW key in your HF Space secrets

## Files Removed

The following files were removed as they're not needed for HF Spaces:

- README_HF.md (duplicate)
- DEPLOYMENT.md (local documentation)
- DEPLOYMENT_SUMMARY.md (local documentation)
- QUICK_START.md (local documentation)
- START_HERE.md (local documentation)
- app.py (not needed, using start.sh)
- setup.sh (redundant with .huggingface/pre-start.sh)
- test-local.sh (local testing only)
- .venv/ (virtual environment)
- vectorstore/ (will be regenerated on HF)

## Your Space URL

After deployment: <https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME>

Good luck! 🎉
